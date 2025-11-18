import cv2
import os
import face_recognition
import time
import threading
from queue import Queue
from face_recognition_system import load_known_faces, recognize_face
from asr import ASRListener
from tts import intimidate_intruder, text_to_speech_async
from llm import IntruderConversationManager

# Suppress ALSA warnings
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def recognize_faces_worker(frame_queue, result_queue, known_faces):
    """
    Worker thread function to perform face recognition on frames from a queue.
    """
    while True:
        frame = frame_queue.get()
        if frame is None:  # Sentinel to stop the thread
            break

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")  # HOG is faster than CNN
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        recognized_faces = []
        # Loop through each face in this frame of video
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # See if the face is a match for the known face(s)
            name = "Unknown"
            if known_faces:
                for person_name, encodings in known_faces.items():
                    matches = face_recognition.compare_faces(encodings, face_encoding, tolerance=0.6)
                    if any(matches):
                        name = person_name
                        break
            
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            recognized_faces.append(((top, right, bottom, left), name))
        
        result_queue.put(recognized_faces)
        # Small delay to give CPU time to other threads (ASR)
        time.sleep(1)

def run_live_recognition(known_faces):
    """
    Uses the live camera feed to perform real-time face recognition in a non-blocking way.
    Also integrates ASR for voice commands.
    """
    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        print("Error: Could not open video stream.")
        return

    video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    frame_queue = Queue(maxsize=1)
    result_queue = Queue(maxsize=1)

    # Start the face recognition worker thread
    recognition_thread = threading.Thread(
        target=recognize_faces_worker,
        args=(frame_queue, result_queue, known_faces)
    )
    recognition_thread.daemon = True
    recognition_thread.start()

    # Initialize ASR listener
    asr_listener = ASRListener()
    asr_listener.start_listening()

    # Initialize conversation manager for intruders
    conversation_manager = IntruderConversationManager()
    conversation_mode = False  # Flag for when we're conversing with intruder
    conversation_timeout = 0  # Timestamp for conversation timeout

    recognized_faces = []
    frame_count = 0
    process_every_n_frames = 3  # Process face recognition every 3 frames to reduce CPU load
    guard_mode = False  # Flag for guard mode
    last_unknown_alert_time = 0  # To prevent spam alerts
    
    # ANSI color codes
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()
        if not ret:
            print("Error: Can't receive frame (stream end?). Exiting ...")
            break

        frame_count += 1
        
        # Put the frame in the queue for the worker thread to process (but not every frame)
        if frame_count % process_every_n_frames == 0:
            if not frame_queue.full():
                frame_queue.put(frame)

        # Check for results from the worker thread
        if not result_queue.empty():
            recognized_faces = result_queue.get()
        
        # Guard mode: Check for unknown faces
        if guard_mode:
            current_time = time.time()
            for (top, right, bottom, left), name in recognized_faces:
                if name == "Unknown" and (current_time - last_unknown_alert_time) > 10:
                    # Print red alert for unknown person
                    print(f"{RED}{BOLD}{'='*60}{RESET}")
                    print(f"{RED}{BOLD}⚠️  ALERT: UNKNOWN PERSON DETECTED! ⚠️{RESET}")
                    print(f"{RED}{BOLD}{'='*60}{RESET}")
                    
                    # Start conversation with intruder if not already in conversation
                    if not conversation_mode:
                        conversation_mode = True
                        conversation_timeout = current_time + 60  # 60 second conversation timeout
                        print(f"{RED}🤖 Starting conversation with intruder...{RESET}")
                        opening_message = conversation_manager.start_conversation()
                        text_to_speech_async(opening_message)
                    
                    last_unknown_alert_time = current_time

        # Draw the results on the frame and display only when guard mode is active
        if guard_mode:
            for (top, right, bottom, left), name in recognized_faces:
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # Display the resulting image only in guard mode
            cv2.imshow('Video', frame)
            
            # Hit 'q' on the keyboard to quit (only when window is visible)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            # Close the video window when guard mode is off
            try:
                cv2.destroyWindow('Video')
            except:
                pass
            # Small delay to prevent high CPU usage when window is not shown
            time.sleep(0.1)

        # Check for speech input from ASR
        if asr_listener.has_text():
            spoken_text = asr_listener.get_text()
            print(f"{YELLOW}[VOICE COMMAND]: {spoken_text}{RESET}")
            
            # If in conversation mode, treat this as intruder response
            if conversation_mode:
                print(f"{RED}[INTRUDER]: {spoken_text}{RESET}")
                ai_response = conversation_manager.process_intruder_response(spoken_text)
                print(f"{GREEN}[SECURITY AI]: {ai_response}{RESET}")
                text_to_speech_async(ai_response)
                # Reset conversation timeout
                conversation_timeout = time.time() + 60
            else:
                # Process voice commands (only when not in conversation)
                spoken_lower = spoken_text.lower()
                
                # Guard my room command
                if "guard" in spoken_lower and "room" in spoken_lower:
                    guard_mode = True
                    print(f"{GREEN}{BOLD}✓ GUARD MODE ACTIVATED{RESET}")
                    print(f"{GREEN}System will alert when unknown faces are detected.{RESET}")
                
                # Stop guard command
                elif "stop" in spoken_lower and "guard" in spoken_lower:
                    guard_mode = False
                    conversation_mode = False
                    if conversation_manager.is_conversation_active():
                        conversation_manager.end_conversation()
                    print(f"{YELLOW}GUARD MODE DEACTIVATED{RESET}")
                
                # Quit/Exit commands
                elif any(word in spoken_lower for word in ["quit", "exit", "close"]):
                    print(f"{YELLOW}Voice command to quit received!{RESET}")
                    break
        
        # Check for conversation timeout
        if conversation_mode and time.time() > conversation_timeout:
            print(f"{YELLOW}⏱️  Conversation timeout. Ending conversation with intruder.{RESET}")
            conversation_mode = False
            if conversation_manager.is_conversation_active():
                print(conversation_manager.get_conversation_summary())
                conversation_manager.end_conversation()
                # Give final warning
                text_to_speech_async("You have not responded. Security has been notified. Leave immediately.")

        # Add other non-blocking functionalities here
        # For example:
        # check_for_user_input()
        # update_gui()

    # Stop ASR listener
    asr_listener.stop_listening()

    # Signal the worker thread to stop and wait for it
    frame_queue.put(None)
    recognition_thread.join()

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(script_dir, "dataset")
    
    known_faces = load_known_faces(dataset_path)
    
    if not known_faces:
        print("No known faces loaded. Please check the dataset directory.")
    else:
        run_live_recognition(known_faces)
