from gtts import gTTS
import pygame
import os
import tempfile
import threading
import time

# Global flag to indicate when TTS is speaking
is_speaking = False
speaking_lock = threading.Lock()

# Initialize pygame mixer for audio playback
pygame.mixer.init()

def is_tts_speaking():
    """
    Check if TTS is currently speaking.
    
    Returns:
        bool: True if TTS is speaking, False otherwise
    """
    global is_speaking
    with speaking_lock:
        return is_speaking

def text_to_speech(text, blocking=True):
    """
    Convert text to speech using gTTS and play it using pygame.
    
    Args:
        text: The text to convert to speech
        blocking: If True, waits for speech to complete. If False, plays in background.
    
    Returns:
        True if successful, False otherwise
    """
    global is_speaking
    
    try:
        print(f"TTS module: Synthesizing speech for text: '{text}'")
        
        # Set speaking flag
        with speaking_lock:
            is_speaking = True
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_file = fp.name
        
        # Generate speech
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(temp_file)
        
        # Load and play the audio
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        
        if blocking:
            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clear speaking flag
            with speaking_lock:
                is_speaking = False
        
        # Clean up the temporary file (after a delay if non-blocking)
        if blocking:
            try:
                os.remove(temp_file)
            except:
                pass
        else:
            # Schedule cleanup after audio finishes for non-blocking
            def cleanup():
                # Wait for audio to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                # Clear speaking flag
                with speaking_lock:
                    is_speaking = False
                
                # Remove temp file
                time.sleep(1)
                try:
                    os.remove(temp_file)
                except:
                    pass
            threading.Thread(target=cleanup, daemon=True).start()
        
        return True
        
    except Exception as e:
        print(f"TTS Error: {e}")
        return False


def text_to_speech_async(text):
    """
    Convert text to speech in a background thread (non-blocking).
    """
    def _speak():
        text_to_speech(text, blocking=True)
    
    thread = threading.Thread(target=_speak, daemon=True)
    thread.start()
    return True


def intimidate_intruder():
    """
    Play an intimidating message to scare away intruders.
    """
    messages = [
        "Alert! Unknown person detected. This area is under surveillance.",
        "Warning! You are being recorded. Please identify yourself.",
        "Security breach detected. Authorities have been notified.",
        "This is a restricted area. Leave immediately or face consequences."
    ]
    
    import random
    message = random.choice(messages)
    print(f"TTS: Playing intimidation message...")
    return text_to_speech_async(message)


if __name__ == "__main__":
    print("=== TTS Module Test ===\n")
    
    print("Test 1: Simple text-to-speech")
    text_to_speak = "Hello, this is a test of the text to speech system."
    success = text_to_speech(text_to_speak)
    if success:
        print("Speech synthesized successfully.\n")
    
    print("Test 2: Intimidation message")
    intimidate_intruder()
    time.sleep(8)  # Wait for async speech to complete
    print("Test complete!")

