import speech_recognition as sr
import threading
import queue
import time
import os
import sys

# Suppress ALSA warnings by redirecting stderr temporarily
class SuppressStderr:
    def __enter__(self):
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for _ in range(2)]
        self.save_fds = [os.dup(2)]
        os.dup2(self.null_fds[0], 2)
    
    def __exit__(self, *_):
        os.dup2(self.save_fds[0], 2)
        for fd in self.null_fds + self.save_fds:
            os.close(fd)

class ASRListener:
    """
    A class to handle Automatic Speech Recognition (ASR) in a non-blocking way.
    Uses a background thread to continuously listen for speech input.
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Initialize microphone with suppressed stderr
        with SuppressStderr():
            self.microphone = sr.Microphone()
        
        self.listening = False
        self.text_queue = queue.Queue()
        self.listen_thread = None
        
        # Adjust recognizer settings for better performance under CPU load
        # Higher threshold to reduce false positives and speaker feedback
        self.recognizer.energy_threshold = 6000  # Increased from 4000 to reduce speaker pickup
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Shorter pause threshold
        
        # Adjust for ambient noise on initialization
        print("ASR: Calibrating microphone for ambient noise...")
        with SuppressStderr():
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("ASR: Ready to listen!")
    
    def _listen_worker(self):
        """
        Worker function that runs in a background thread to listen for speech.
        """
        while self.listening:
            try:
                # Check if TTS is speaking to avoid feedback loop
                try:
                    from tts import is_tts_speaking
                    if is_tts_speaking():
                        print("ASR: Pausing (TTS is speaking)...")
                        time.sleep(0.5)
                        continue
                except ImportError:
                    pass  # If tts module not available, continue normally
                
                with SuppressStderr():
                    with self.microphone as source:
                        # Listen for audio input with a timeout
                        print("ASR: Listening...")
                        audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                    
                try:
                    # Recognize speech using Google Speech Recognition
                    print("ASR: Processing audio...")
                    text = self.recognizer.recognize_google(audio)
                    print(f"ASR: Recognized: '{text}'")
                    self.text_queue.put(text)
                except sr.UnknownValueError:
                    print("ASR: Could not understand audio")
                except sr.RequestError as e:
                    print(f"ASR: Could not request results; {e}")
                    
            except sr.WaitTimeoutError:
                # Timeout occurred, just continue listening
                pass
            except Exception as e:
                print(f"ASR: Error in listening loop: {e}")
                time.sleep(1)  # Prevent rapid error loops
    
    def start_listening(self):
        """
        Start listening for speech in a background thread.
        """
        if not self.listening:
            self.listening = True
            self.listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
            self.listen_thread.start()
            print("ASR: Started listening in background")
    
    def stop_listening(self):
        """
        Stop the background listening thread.
        """
        if self.listening:
            self.listening = False
            if self.listen_thread:
                self.listen_thread.join(timeout=2)
            print("ASR: Stopped listening")
    
    def get_text(self):
        """
        Get recognized text from the queue if available.
        Returns None if no text is available.
        """
        try:
            return self.text_queue.get_nowait()
        except queue.Empty:
            return None
    
    def has_text(self):
        """
        Check if there is recognized text available in the queue.
        """
        return not self.text_queue.empty()


def recognize_speech_once():
    """
    Simple function to recognize speech once (blocking).
    Useful for standalone ASR testing.
    """
    recognizer = sr.Recognizer()
    
    with SuppressStderr():
        microphone = sr.Microphone()
    
        print("Adjusting for ambient noise... Please wait.")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("Listening... Speak now!")
        with microphone as source:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("Processing audio...")
                
                # Recognize speech using Google Speech Recognition
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
                
            except sr.WaitTimeoutError:
                print("Listening timed out. No speech detected.")
                return None
            except sr.UnknownValueError:
                print("Could not understand the audio.")
                return None
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                return None


if __name__ == "__main__":
    print("=== ASR Module Test ===")
    print("\nTest 1: Single recognition (blocking)")
    result = recognize_speech_once()
    if result:
        print(f"Recognition successful: '{result}'")
    
    print("\n\nTest 2: Continuous listening (non-blocking)")
    print("This will listen for 15 seconds. Press Ctrl+C to stop early.")
    
    listener = ASRListener()
    listener.start_listening()
    
    try:
        start_time = time.time()
        while time.time() - start_time < 15:
            if listener.has_text():
                text = listener.get_text()
                print(f">>> Received: '{text}'")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        listener.stop_listening()
        print("Test complete!")
