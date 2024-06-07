from flask import Flask, request, jsonify, send_from_directory
import base64
import cv2
import numpy as np
import mediapipe as mp
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')

# Initialize MediaPipe Holistic
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(static_image_mode=False, min_detection_confidence=0.5)
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
    results = holistic.process(frame_rgb)

    circle_details = []

    # Process hand landmarks and left elbow
    if results.left_hand_landmarks or results.right_hand_landmarks:
        # ... (existing code for right hand)

        if results.left_hand_landmarks:
            # Processing for left hand
            left_hand_landmarks = results.left_hand_landmarks
            wrist = left_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST]
            wrist_coords = (int(wrist.x * frame.shape[1]), int(wrist.y * frame.shape[0]))

            index_tip = left_hand_landmarks.landmark[mp_holistic.HandLandmark.INDEX_FINGER_TIP]
            index_tip_coords = (int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0]))
            circle_size = calculate_circle_size(index_tip_coords, wrist_coords)
            cv2.circle(frame, index_tip_coords, circle_size, (128, 128, 128), -1)

            circle_details.append({
                'x': index_tip_coords[0], 
                'y': index_tip_coords[1], 
                'size': circle_size
            })

            # Draw left elbow and connect with line
            if results.pose_landmarks:
                elbow = results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_ELBOW]
                elbow_coords = (int(elbow.x * frame.shape[1]), int(elbow.y * frame.shape[0]))
                cv2.circle(frame, elbow_coords, 5, (0, 255, 0), -1)  # Green circle for elbow
                cv2.line(frame, elbow_coords, index_tip_coords, (255, 0, 0), 2)  # Blue line connecting elbow and fingertip


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
    return send_from_directory(app.static_folder, 'index-camera-two-circles.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
