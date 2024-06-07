from flask import Flask, request, jsonify, send_from_directory
import base64
import cv2
import numpy as np
import mediapipe as mp
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')

# Initialize MediaPipe Holistic.
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(static_image_mode=False, min_detection_confidence=0.5)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    image_string = data['image']
    image_data = base64.b64decode(image_string.split(',')[1])
    nparr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = holistic.process(frame_rgb)

    landmarks = []
    connections = []

    if results.pose_landmarks:
        # Extract landmarks
        for id, landmark in enumerate(results.pose_landmarks.landmark):
            landmarks.append({
                'id': id,
                'x': landmark.x,
                'y': landmark.y,
                'z': landmark.z,
                'visibility': landmark.visibility
            })

        # Extract connections
        for connection in mp_holistic.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            connections.append({
                'start': landmarks[start_idx],  # Start landmark
                'end': landmarks[end_idx],      # End landmark
            })

    return jsonify({'landmarks': landmarks, 'connections': connections})

@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.json
    image_string = data['image']
    image_data = base64.b64decode(image_string.split(',')[1])
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
    image_path = os.path.join('D:/planets-camera/static/images', filename)
    if not os.path.exists(os.path.dirname(image_path)):
        os.makedirs(os.path.dirname(image_path))
    with open(image_path, 'wb') as file:
        file.write(image_data)
    return jsonify({'status': 'Image saved', 'filename': filename})

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index-camera-holistic.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
