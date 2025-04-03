import cv2
import face_recognition
import numpy as np
import os
from database import create_tables, insert_attendance, insert_image

# Create tables in the database
create_tables()

base_dir = os.path.dirname(os.path.abspath(__file__)) 
known_faces_folder = os.path.join(base_dir, "img_align_celeba")
check_attendance_folder = os.path.join(base_dir, "check_attendance")

known_face_encodings = []
known_face_names = []

if not os.path.exists(known_faces_folder):
    print(f"Error: Folder '{known_faces_folder}' does not exist.")
    exit()

image_files = [f for f in os.listdir(known_faces_folder) if f.endswith(".jpg")]
if not image_files:
    print("Error: No images found in the dataset.")
    exit()

for filename in image_files:
    name = os.path.splitext(filename)[0]
    image_path = os.path.join(known_faces_folder, filename)
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if len(encodings) == 1:
        known_face_encodings.append(encodings[0])
        known_face_names.append(name)
    else:
        print(f"Warning: No face or multiple faces found in '{filename}'. Skipping.")

if not known_face_names:
    print("Warning: No known faces found.")

if not os.path.exists(check_attendance_folder):
    print(f"Error: Folder '{check_attendance_folder}' does not exist.")
    exit()

attendance_image_files = [f for f in os.listdir(check_attendance_folder) if f.endswith(".jpg")]
if not attendance_image_files:
    print("Error: No images found in the check_attendance folder.")
    exit()

present_names = set()

for attendance_file in attendance_image_files:
    attendance_image_path = os.path.join(check_attendance_folder, attendance_file)
    img = cv2.imread(attendance_image_path)
    if img is None:
        print(f"Error: Could not load image {attendance_file}. Skipping.")
        continue

    with open(attendance_image_path, 'rb') as file:
        image_data = file.read()
        insert_image(attendance_file, image_data)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(img_rgb)
    face_encodings = face_recognition.face_encodings(img_rgb, face_locations)

    for face_encoding in face_encodings:
        distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        name = "Unknown"
        if len(distances) > 0:
            min_distance_index = np.argmin(distances)
            if distances[min_distance_index] < 0.6:
                name = known_face_names[min_distance_index]
                present_names.add(name)

all_students = set(known_face_names)
absent_names = all_students - present_names

present_names = sorted(present_names, key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else float('inf'))
absent_names = sorted(absent_names, key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else float('inf'))

print("Present:", ", ".join(present_names) if present_names else "None")
print("Absent:", ", ".join(absent_names) if absent_names else "None")

for name in present_names:
    insert_attendance(name, 'Present')
for name in absent_names:
    insert_attendance(name, 'Absent')
