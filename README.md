# Face Recognition Guard System

This project is an intelligent security system that uses real-time face recognition to identify known and unknown individuals. It features voice command activation and a conversational AI to interact with potential intruders.

## Features

- **Real-Time Face Recognition**: Identifies faces from a live webcam feed.
- **Voice-Controlled Operation**: Activate and deactivate the guard mode using voice commands like "guard my room" and "stop guard".
- **Intruder Interaction**: When an unknown person is detected, the system initiates a conversation using a large language model (LLM) to challenge and interact with them.
- **Text-to-Speech (TTS)**: The system provides audible alerts and speaks the AI's responses.
- **Automatic Speech Recognition (ASR)**: Listens for voice commands and intruder responses.
- **Efficient Processing**: Uses a multi-threaded architecture to process video frames without lagging the main application.

## How It Works

The system is composed of several modules working in tandem:
1.  **Video Capture**: Captures frames from the webcam.
2.  **Face Recognition Engine**: A worker thread processes video frames to detect and identify faces against a pre-enrolled database of known individuals.
3.  **ASR/TTS**: The system listens for commands and speaks alerts or messages.
4.  **Conversation Manager**: If an unknown person is detected, an LLM-based conversational agent engages with the person.
5.  **Main Application**: The main script orchestrates these components, allowing the user to toggle "guard mode" and displaying the video feed with recognized faces.

## Prerequisites

- Python 3.8+
- A webcam and a microphone

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd aml_assignment2
    ```

2.  **Create a Conda environment (recommended):**
    It is highly recommended to use a Conda environment to manage the complex dependencies like `dlib` and `opencv`.
    ```bash
    conda create --name guard_system python=3.10
    conda activate guard_system
    ```

3.  **Install dependencies:**
    Install the core packages using conda, preferably from the `conda-forge` channel for better compatibility.
    ```bash
    conda install -c conda-forge dlib opencv pyaudio
    ```
    Then, install the remaining Python packages using pip:
    ```bash
    pip install face_recognition
    ```
    *(You may need to install other packages from a `requirements.txt` file if one is provided).*

## Usage

1.  **Enroll Users**:
    Before running the main system, you need to enroll the faces of known individuals. Run the `enroll_user.py` script and follow the on-screen instructions. This will capture images and save them to the `dataset` directory.
    ```bash
    python enroll_user.py
    ```

2.  **Run the Guard System**:
    Start the main application by running `main.py`.
    ```bash
    python main.py
    ```

3.  **Voice Commands**:
    - **"Guard my room"**: Activates the security monitoring. The system will start displaying the video feed and will alert you if an unknown person is detected.
    - **"Stop guard"**: Deactivates the security monitoring.
    - **"Quit" / "Exit"**: Terminates the application.

You can also press the 'q' key when the video window is active to quit the application.
