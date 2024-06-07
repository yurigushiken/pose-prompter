from flask import Flask, request, jsonify, send_from_directory
import base64
import cv2
import numpy as np
import mediapipe as mp
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')

# Initialize MediaPipe Hands.
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

def calculate_circle_size(index_tip, wrist):
    distance = np.linalg.norm(np.array(index_tip) - np.array(wrist))
    # Increase the scaling factor from 0.5 to a higher value, like 1.0 or more, to make the circle larger.
    circle_size = int(distance * .10)  # Adjust the multiplier as needed
    return max(circle_size, 5)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    image_string = data['image']
    image_data = base64.b64decode(image_string.split(',')[1])
    nparr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    circle_details = []

    if results.multi_hand_landmarks and results.multi_handedness:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            hand_label = results.multi_handedness[idx].classification[0].label
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

            index_tip_coords = (int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0]))
            wrist_coords = (int(wrist.x * frame.shape[1]), int(wrist.y * frame.shape[0]))

            circle_size = calculate_circle_size(index_tip_coords, wrist_coords)
            cv2.circle(frame, index_tip_coords, circle_size, (128, 128, 128), -1)

            circle_details.append({
                'x': index_tip_coords[0], 
                'y': index_tip_coords[1], 
                'size': circle_size,
                'hand_side': hand_label
            })

    return jsonify({'fingertip_details': circle_details})

@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.json
    image_string = data['image']
    image_data = base64.b64decode(image_string.split(',')[1])
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
    image_path = os.path.join('D:/planets-camera/static/images', filename)
    with open(image_path, 'wb') as file:
        file.write(image_data)
    return jsonify({'status': 'Image saved', 'filename': filename})

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index-camera-L-circle-R-color.html')

if __name__ == '__main__':
    app.run(debug=True, port=5003)
