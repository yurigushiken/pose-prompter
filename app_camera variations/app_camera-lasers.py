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

def calculate_line_thickness(index_tip, joint):
    distance = np.linalg.norm(np.array(index_tip) - np.array(joint))
    # Adjust the scaling factor as needed to change the starting thickness
    line_thickness = int(distance * .40)  
    return max(line_thickness, 1)  # Ensure a minimum thickness

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    image_string = data['image']
    image_data = base64.b64decode(image_string.split(',')[1])
    nparr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    line_length = 1000 

    line_details = []

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Define common anchor point as the midpoint between the wrist and middle finger MCP
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            middle_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
            anchor_point = (
                int((wrist.x + middle_finger_mcp.x) * 0.5 * frame.shape[1]),
                int((wrist.y + middle_finger_mcp.y) * 0.5 * frame.shape[0])
            )

            # Process for Index Finger
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            process_finger(index_tip, anchor_point, line_length, line_details, frame.shape)

            # Process for Thumb
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            process_finger(thumb_tip, anchor_point, line_length, line_details, frame.shape)

    return jsonify({'line_details': line_details})

def process_finger(tip, anchor_point, line_length, line_details, frame_shape):
    tip_coords = (int(tip.x * frame_shape[1]), int(tip.y * frame_shape[0]))

    direction = np.array(tip_coords) - np.array(anchor_point)
    angle = np.arctan2(direction[1], direction[0]) * 180 / np.pi

    # Determine if line should be horizontal or vertical
    # Round to the nearest horizontal or vertical direction
    if -45 <= angle < 45 or 135 <= angle < 225:
        # Make the line horizontal
        end_x = anchor_point[0] + (np.sign(direction[0]) * line_length)
        end_y = anchor_point[1]
    else:
        # Make the line vertical
        end_x = anchor_point[0]
        end_y = anchor_point[1] + (np.sign(direction[1]) * line_length)

    line_thickness = calculate_line_thickness(tip_coords, anchor_point)

    # Add line detail
    line_details.append({
        'start_x': anchor_point[0],
        'start_y': anchor_point[1],
        'end_x': int(end_x),
        'end_y': int(end_y),
        'thickness': line_thickness
    })


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
    return send_from_directory(app.static_folder, 'index-camera-lasers.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
