import os
import face_recognition
import time

def load_known_faces(dataset_path):
    """
    Loads known faces from the dataset directory.
    """
    known_faces = {}
    for person_name in os.listdir(dataset_path):
        person_dir = os.path.join(dataset_path, person_name)
        if os.path.isdir(person_dir):
            encodings = []
            for image_name in os.listdir(person_dir):
                image_path = os.path.join(person_dir, image_name)
                try:
                    image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(image)
                    if face_encodings:
                        encodings.append(face_encodings[0])
                except Exception as e:
                    print(f"Error processing image {image_path}: {e}")
            if encodings:
                known_faces[person_name] = encodings
    return known_faces

def recognize_face(unknown_image_path, known_faces):
    """
    Recognizes a face in an image by comparing it to a known faces dataset.
    """
    try:
        unknown_image = face_recognition.load_image_file(unknown_image_path)
        unknown_face_encodings = face_recognition.face_encodings(unknown_image)

        if not unknown_face_encodings:
            print(f"Error: No face found in the user image ('{os.path.basename(unknown_image_path)}').")
            return None

        unknown_encoding = unknown_face_encodings[0]

        for person_name, encodings in known_faces.items():
            matches = face_recognition.compare_faces(encodings, unknown_encoding)
            if any(matches):
                return person_name
        
        return "Unknown"

    except FileNotFoundError as e:
        print(f"Error loading image file: {e}")
        return None

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(script_dir, "dataset")
    unknown_image_path = os.path.join(script_dir, "images/user_image.jpg")

    start_time = time.time()
    known_faces = load_known_faces(dataset_path)
    
    if not known_faces:
        print("No known faces loaded. Please check the dataset directory.")
    else:
        person = recognize_face(unknown_image_path, known_faces)
        end_time = time.time()

        if person:
            print(f"The person in the image is: {person}")
        
        print(f"Execution time: {end_time - start_time:.4f} seconds")