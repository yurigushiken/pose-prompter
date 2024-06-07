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
import base64
import random
import uuid
import time
from PIL import Image
import io


custom_canny_image = None
is_generating_continuously = False

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

watcher_thread = threading.Thread(target=start_observer)
watcher_thread.daemon = True
watcher_thread.start()


def combine_images(image_path, image_data):
    try:
        with Image.open(image_path) as img1, Image.open(image_data) as img2:
            # Assuming both images have the same dimensions
            combined_image = Image.new('RGBA', img1.size)
            combined_image.paste(img1, (0, 0), img1)
            combined_image.paste(img2, (0, 0), img2)
            return combined_image
    except IOError as e:
        print(f"Error in combining images: {e}")
        return None
    
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
    global custom_canny_image

    while is_generating_continuously or (not is_generating_continuously and json_data):
        try:
            with open('D:/consolidation/workflows/workflow_desertUSAcanny.json', 'r') as file:
                workflow = json.load(file)

            latest_image_path = get_latest_image('D:/planets-camera/static/images')
            if latest_image_path and custom_canny_image:
                # Strip data URL prefix if present in custom_canny_image
                custom_canny_image_data = custom_canny_image.split(',')[1] if ',' in custom_canny_image else custom_canny_image
                
                # Decode the base64 string of custom_canny_image to an image
                custom_image_data = io.BytesIO(base64.b64decode(custom_canny_image_data))
                combined_image = combine_images(latest_image_path, custom_image_data)
                if combined_image:
                    buffered = io.BytesIO()
                    combined_image.save(buffered, format="PNG")
                    combined_base64 = base64.b64encode(buffered.getvalue()).decode()

                    # Ensure proper padding
                    combined_base64 += '=' * (-len(combined_base64) % 4)
                    workflow["49"]["inputs"]["image"] = combined_base64


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
            time.sleep(0.65)

        except json.JSONDecodeError as e:
            print(f"Error loading JSON: {e}")
            return



@socketio.on('upload_image')
def handle_upload_image(data):
    global custom_canny_image
    if 'image' in data:
        # Assuming the client sends the base64 string without the 'data:image/png;base64,' prefix
        base64_data = data['image']
        try:
            # This is just a validation step to ensure the image can be decoded
            Image.open(io.BytesIO(base64.b64decode(base64_data))).verify()
            # If it's valid, store it in custom_canny_image
            custom_canny_image = base64_data
        except (IOError, ValueError, binascii.Error) as e:
            print(f"Error with the uploaded image data: {e}")
            custom_canny_image = None

        # If 'image' is the file object itself:
        # custom_canny_image = base64.b64encode(data['image'].read()).decode()

        # Optional: Validate the image by attempting to open it with PIL
        try:
            Image.open(io.BytesIO(base64.b64decode(custom_canny_image))).show()
        except (IOError, ValueError) as e:
            print(f"Error decoding or identifying the base64 image: {e}")
            custom_canny_image = None


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)