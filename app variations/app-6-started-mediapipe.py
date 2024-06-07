import json
import requests
import struct
import threading
import asyncio
import websockets
from flask import Flask, render_template
from flask_socketio import SocketIO
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from io import BytesIO
import base64
import random
import uuid
import json
import urllib.request
import urllib.parse
import uuid
import time
import mediapipe as mp
import cv2
import numpy as np

is_generating_continuously = False

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

# Initialize Flask App
app = Flask(__name__, static_folder='D:/planets/static')
socketio = SocketIO(app, cors_allowed_origins='*')

# Function to get the latest image from a directory
def get_latest_image(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files[0] if files else None

# Event handler class for new file creation
class LatestFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            global latest_image_path_global
            latest_image_path_global = event.src_path

# Start file observer
def start_observer():
    path = 'D:/planets-camera/static/images'
    event_handler = LatestFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

# Start the watcher thread
watcher_thread = threading.Thread(target=start_observer)
watcher_thread.daemon = True
watcher_thread.start()


# Function to handle WebSocket communication
def handle_websocket_communication(json_data):
    server_address = "127.0.0.1:8188"
    client_id = str(uuid.uuid4())
    ws = websocket.WebSocket()
    ws.connect(f"ws://{server_address}/ws?clientId={client_id}")

    # Send prompt to ComfyUI
    prompt = json_data  # Assuming json_data is the prompt
    ws.send(json.dumps(prompt))

    # Listen for responses
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executed':
                # Prompt execution done, you can break or handle further as needed
                break
        elif isinstance(out, bytes):
            # Handle binary data (image)
            image_data = out  # Assuming the entire message is the image data
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            socketio.emit('image_data', {'type': 'binary', 'data': image_base64})

# Threaded function to handle WebSocket communication
def start_websocket_thread(json_data):
    threading.Thread(target=handle_websocket_communication, args=(json_data,)).start()


# Route for index page
@app.route('/')
def index():
    return render_template('index.html')

# WebSocket listener function
async def listen_for_images():
    uri = f"ws://127.0.0.1:8188/ws?clientId={client_id}"
    async with websockets.connect(uri) as ws:
        async for msg in ws:
            if isinstance(msg, bytes):
                s = struct.calcsize(">II")
                if len(msg) > s:
                    event, format = struct.unpack_from(">II", msg, 0)
                    if event == 1 and format == 2:  # Check for Preview Image in PNG format
                        image_data = msg[s:]
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        socketio.emit('image_data', {'type': 'binary', 'data': image_base64})

# Function to start the WebSocket listener in a new thread
def start_websocket_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen_for_images())
    loop.close()

# Start WebSocket listener in a separate thread
websocket_listener_thread = threading.Thread(target=start_websocket_listener, daemon=True)
websocket_listener_thread.start()

@socketio.on('toggle_continuous_generation')
def handle_toggle_continuous_generation(data):
    global is_generating_continuously
    is_generating_continuously = data['isContinuous']

@socketio.on('generate_image')
def handle_generate_image(json_data):
    global is_generating_continuously

    while is_generating_continuously or not is_generating_continuously and json_data:
        try:
            with open('D:/planets/workflow_base64.json', 'r') as file:
                workflow = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error loading JSON: {e}")
            return

        latest_image_path = get_latest_image('D:/planets-camera/static/images')
        if latest_image_path:
            with open(latest_image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                workflow["49"]["inputs"]["image"] = encoded_string

                # Process the image for hand tracking and modify the prompt
                right_hand_y = process_hand_frame(encoded_string)
                if right_hand_y is not None:
                    # Adjust the prompt based on hand position
                    color_prompt = ' red' if right_hand_y < 0.5 else ' pink'
                    workflow["2"]["inputs"]["text"] = json_data['prompt'] + color_prompt
                else:
                    workflow["2"]["inputs"]["text"] = json_data['prompt']

        workflow["4"]["inputs"]["noise_seed"] = random.randint(1, 18446744073709551615)

        url = "http://127.0.0.1:8188/prompt"
        headers = {'Content-Type': 'application/json'}
        socketio.emit('image_started')
        response = requests.post(url, json={"prompt": workflow}, headers=headers)

        if response.status_code != 200:
            error_message = f'Failed to generate image: {response.text}'
            socketio.emit('image_error', {'error': error_message})
        else:
            socketio.emit('image_complete')

        if not is_generating_continuously:
            break
        time.sleep(0.2)  # Adjust this value as needed for the rate of generation

def process_hand_frame(image_data):
    # Decode the image
    nparr = np.frombuffer(base64.b64decode(image_data.split(',')[1]), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe
    results = hands.process(frame_rgb)
    right_hand_y = None

    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            hand_label = 'Right' if idx == 0 else 'Left'  # Assuming the first detected hand is right
            if hand_label == 'Right':
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                right_hand_y = index_tip.y  # y coordinate of the right index fingertip

    return right_hand_y


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)
