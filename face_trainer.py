import os
import face_recognition
import pickle

TRAINING_DIR = "training_images"
MODEL_FILE = "face_recognition_model/model.pkl"

known_faces = []
known_names = []

for person in os.listdir(TRAINING_DIR):
    person_dir = os.path.join(TRAINING_DIR, person)
    for img_name in os.listdir(person_dir):
        img_path = os.path.join(person_dir, img_name)
        img = face_recognition.load_image_file(img_path)
        encodings = face_recognition.face_encodings(img)

        if encodings:
            known_faces.append(encodings[0])
            known_names.append(person)

with open(MODEL_FILE, "wb") as f:
    pickle.dump((known_faces, known_names), f)

print("Model Training Completed!")
