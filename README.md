# Pose Prompter

This repository contains the code for the Pose Prompter, a final project submission for A&HA-4084 at Teachers College. The Pose Prompter is an innovative system that combines real-time hand tracking with automated image generation, allowing users to generate images based on their pose in front of a webcam and a text prompt.

## Project Overview

The Pose Prompter operates in two main components:

1. **Camera Component**: Handles real-time hand tracking using a webcam.
2. **Image Generation Component**: Uses the captured screenshots and text prompts to generate images.

### Technologies Used

- **GPT-4**: For writing code and software walkthrough.
- **VS Code**: For code writing and file management.
- **GitHub**: For version control and community assistance.
- **MediaPipe**: For body tracking.
- **ComfyUI**: For image generation (a version of Stable Diffusion).
- **Flask**: For building the web server.
- **Socket.io**: For real-time communication between the frontend and backend.

## Components

### Camera Component

This component includes two files: `app_camera.py` and `index-camera.html`.

- **`app_camera.py`**: 
  - Processes video frames from the webcam.
  - Uses MediaPipe to detect hand landmarks.
  - Draws circles on detected hand areas.
  - Captures and saves screenshots every 200ms.

- **`index-camera.html`**: 
  - Displays the webcam feed.
  - Shows the JavaScript overlay of circles on detected hand areas.
  - Captures screenshots and sends them to the backend for processing.

### Image Generation Component

This component includes two files: `app.py` and `index.html`.

- **`app.py`**:
  - Monitors the screenshot-save directory for the newest file.
  - Sends the latest screenshot and a text prompt to ComfyUI.
  - Handles image generation requests and updates the frontend with generated images.

- **`index.html`**:
  - Provides the interface for inputting text prompts.
  - Displays the generated images in real-time.
  - Allows for continuous image generation.

### Sample Videos

- **Dual Planetary Dance**:

  [![Dual Planetary Dance](https://img.youtube.com/vi/eyOeO71i9Yo/0.jpg)](https://youtu.be/eyOeO71i9Yo)

- **Moon over Horizon**:

  [![Moon over Horizon](https://img.youtube.com/vi/vMOaVY5-riU/0.jpg)](https://youtu.be/vMOaVY5-riU)

- **Celestial Being**:

  [![Celestial Being](https://img.youtube.com/vi/eyOeO71i9Yo/0.jpg)](https://youtu.be/eyOeO71i9Yo)



## Installation and Setup

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/mkg2145/pose-prompter.git
    cd pose-prompter
    ```

2. **Install Dependencies**:
    Ensure you have the required Python packages:
    ```bash
    pip install flask flask_socketio requests watchdog mediapipe opencv-python
    ```

3. **Set Up Directories**:
    Ensure you have the following directory structure for the images:
    ```plaintext
    pose-prompter/
    ├── app variations/
    │   ├── static/
    │   │   └── images/
    │   │       ├── combined/
    │   │       └── user-uploaded/
    │   └── workflows/
    └── app_camera variations/
        └── static/
            └── images/
    ```

4. **Run the Camera Component**:
    ```bash
    cd app_camera\ variations
    python app_camera.py
    ```

5. **Run the Image Generation Component**:
    ```bash
    cd ../app\ variations
    python app.py
    ```

6. **Open the Application**:
    - For real-time hand tracking, navigate to `http://localhost:5002`.
    - For image generation, navigate to `http://localhost:5001`.

## Usage

- **Real-time Hand Tracking**:
  - Open `http://localhost:5002` to view the webcam feed and hand tracking overlays.
  - Adjust your pose to see the overlays and capture screenshots.

- **Image Generation**:
  - Open `http://localhost:5001` to enter text prompts and view generated images.
  - Use the slider to adjust the color and generate new images based on your prompt and pose.

## Example Workflows

- **Moon over Horizon**
- **A Being in the Universe**
- **Two Planets in a Cloudy Universe**

## Inspiration

The project was inspired by the release of SDXL Turbo, which allows for near-real-time image generation.

## Acknowledgments

- **Professor James Dec, Teachers College, Columbia University**: For the course and project opportunity.
- **ComfyUI Community**: For support and resources.

## Contact

- **Yuri Gushiken**: [mischagushiken@gmail.com](mailto:mischagushiken@gmail.com)

For more detailed information, visit [Yuri's Professional Site](https://yurigushiken.github.io/).
