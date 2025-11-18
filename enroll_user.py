import cv2
import os
import time

# Get the script directory and set dataset path relative to it
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(script_dir, "dataset")

# Create dataset directory if it doesn't exist
if not os.path.exists(dataset_dir):
    os.makedirs(dataset_dir)
    print(f"Created dataset directory: {dataset_dir}")

# Get the person's name
print("="*60)
print("FACE ENROLLMENT SYSTEM")
print("="*60)
print(f"Dataset location: {dataset_dir}\n")
person_name = input("Enter the person's name to enroll: ").strip()

if not person_name:
    print("Error: Name cannot be empty.")
    exit(1)

# Create directory for this person if it doesn't exist
person_dir = os.path.join(dataset_dir, person_name)
if not os.path.exists(person_dir):
    os.makedirs(person_dir)
    print(f"Created new person directory: {person_dir}")
else:
    print(f"Adding image to existing person: {person_name}")

# Count existing images for this person to create unique filename
existing_images = [f for f in os.listdir(person_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
image_number = len(existing_images) + 1

# File path for the new image
file_name = f"{person_name}_{image_number}.jpg"
file_path = os.path.join(person_dir, file_name)

# Initialize webcam
video_capture = cv2.VideoCapture(0)

if not video_capture.isOpened():
    print("Error: Could not open webcam.")
else:
    print(f"\nWebcam opened. Instructions:")
    print("  - Press 'c' to capture the image")
    print("  - Press 'q' to quit without capturing")
    print("  - Window will auto-capture after 10 seconds if no key is pressed\n")
    
    start_time = time.time()
    capture_success = False
    timeout = 10  # seconds

    while time.time() - start_time < timeout:
        # Capture frame-by-frame
        ret, frame = video_capture.read()
        original_frame = frame.copy()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        # Add text overlay showing remaining time and instructions
        remaining_time = int(timeout - (time.time() - start_time))
        cv2.putText(frame, f"Press 'c' to capture | 'q' to quit", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Auto-capture in: {remaining_time}s", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Enrolling: {person_name}", 
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Display the resulting frame
        cv2.imshow('Face Enrollment', frame)

        # Wait for key press
        key = cv2.waitKey(1) & 0xFF
        
        # 'c' key to capture
        if key == ord('c'):
            cv2.imwrite(file_path, original_frame)
            print(f"✓ Image saved to {file_path}")
            capture_success = True
            break
        
        # 'q' key to quit
        elif key == ord('q'):
            print("Enrollment cancelled by user.")
            video_capture.release()
            cv2.destroyAllWindows()
            exit(0)
    
    if not capture_success and ret:
        # If time runs out, save the last frame automatically
        cv2.imwrite(file_path, frame)
        print(f"✓ Auto-captured! Image saved to {file_path}")
        capture_success = True

    # When everything is done, release the capture and destroy windows
    video_capture.release()
    cv2.destroyAllWindows()
    print("\nWebcam closed.")
    
    if capture_success:
        print("="*60)
        print(f"SUCCESS! {person_name} has been enrolled with {image_number} image(s).")
        print(f"Total images for {person_name}: {image_number}")
        print("="*60)
        
        # Ask if user wants to add another image
        add_more = input("\nDo you want to add another image for this person? (y/n): ").strip().lower()
        if add_more == 'y':
            print(f"\nRun this script again and enter '{person_name}' to add more images.")

