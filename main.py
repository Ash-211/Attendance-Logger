import cv2
import face_recognition
import numpy as np
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from database import create_tables, insert_attendance, insert_image, add_student, remove_student, update_student, get_all_students, get_attendance_by_date
import pandas as pd
from datetime import datetime
from tkinter import simpledialog, messagebox, filedialog

create_tables()

base_dir = os.path.dirname(os.path.abspath(__file__)) 
known_faces_folder = os.path.join(base_dir, "img_align_celeba")

known_face_encodings = []
known_face_names = []

def load_known_faces():
    global known_face_encodings, known_face_names
    known_face_encodings = []
    known_face_names = []

    if not os.path.exists(known_faces_folder):
        messagebox.showerror("Error", f"Folder '{known_faces_folder}' does not exist.")
        return False

    image_files = [f for f in os.listdir(known_faces_folder) if f.endswith(".jpg")]
    if not image_files:
        messagebox.showerror("Error", "No images found in the dataset.")
        return False

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
        messagebox.showwarning("Warning", "No known faces found.")
    return True

def start_video_attendance():
    if not load_known_faces():
        return

    video_capture = cv2.VideoCapture(0)
    present_names = set()

    print("Starting video capture. Press 'q' to quit.")

    cv2.namedWindow('Video Attendance', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Video Attendance', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame. Exiting.")
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            name = "Unknown"
            if len(distances) > 0:
                min_distance_index = np.argmin(distances)
                if distances[min_distance_index] < 0.6:
                    name = known_face_names[min_distance_index]
                    present_names.add(name)

        for (top, right, bottom, left), name in zip(face_locations, [known_face_names[np.argmin(face_recognition.face_distance(known_face_encodings, fe))] if len(known_face_encodings) > 0 else "Unknown" for fe in face_encodings]):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

        cv2.imshow('Video Attendance', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

    all_students = set(known_face_names)
    absent_names = all_students - present_names

    present_names_sorted = sorted(present_names, key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else float('inf'))
    absent_names_sorted = sorted(absent_names, key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else float('inf'))

    print("Present:", ", ".join(present_names_sorted) if present_names_sorted else "None")
    print("Absent:", ", ".join(absent_names_sorted) if absent_names_sorted else "None")

    for name in present_names_sorted:
        insert_attendance(name, 'Present')
    for name in absent_names_sorted:
        insert_attendance(name, 'Absent')

    messagebox.showinfo("Attendance", f"Present: {', '.join(present_names_sorted) if present_names_sorted else 'None'}\nAbsent: {', '.join(absent_names_sorted) if absent_names_sorted else 'None'}")
    refresh_student_list()

def refresh_student_list():
    students = get_all_students()
    student_listbox.delete(0, tk.END)
    for name, prn in students:
        student_listbox.insert(tk.END, f"{name} ({prn})")

def add_student_gui():
    name = name_entry.get().strip()
    prn = prn_entry.get().strip()
    if not name or not prn:
        messagebox.showwarning("Input Error", "Please enter both name and PRN.")
        return

    # Check if student already exists
    students = get_all_students()
    for s_name, s_prn in students:
        if s_prn == prn:
            messagebox.showerror("Error", "Student with this PRN already exists.")
            return

    # Capture image from webcam
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Capture Student Image - Press 'c' to capture", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Capture Student Image - Press 'c' to capture", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    messagebox.showinfo("Capture Image", "Press 'c' to capture image, 'q' to cancel.")
    captured_image = None
    while True:
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to access webcam.")
            cap.release()
            cv2.destroyAllWindows()
            return
        cv2.imshow("Capture Student Image - Press 'c' to capture", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            captured_image = frame
            break
        elif key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return
    cap.release()
    cv2.destroyAllWindows()

    if captured_image is None:
        messagebox.showwarning("Capture Cancelled", "No image captured.")
        return

    # Save image to known_faces_folder
    if not os.path.exists(known_faces_folder):
        os.makedirs(known_faces_folder)
    image_filename = f"{prn}.jpg"
    image_path = os.path.join(known_faces_folder, image_filename)
    cv2.imwrite(image_path, captured_image)

    # Insert image into database
    with open(image_path, 'rb') as file:
        image_data = file.read()
        insert_image(image_filename, image_data)

    # Add student to database
    if add_student(name, prn):
        messagebox.showinfo("Success", "Student added successfully.")
        refresh_student_list()
    else:
        messagebox.showerror("Error", "PRN already exists.")
        # Remove saved image if student add failed
        if os.path.exists(image_path):
            os.remove(image_path)

    name_entry.delete(0, tk.END)
    prn_entry.delete(0, tk.END)

def remove_student_gui():
    selected = student_listbox.curselection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a student to remove.")
        return
    student_text = student_listbox.get(selected[0])
    prn = student_text.split('(')[-1].strip(')')
    remove_student(prn)
    messagebox.showinfo("Success", "Student removed successfully.")
    refresh_student_list()

def modify_student_gui():
    selected = student_listbox.curselection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a student to modify.")
        return
    student_text = student_listbox.get(selected[0])
    old_prn = student_text.split('(')[-1].strip(')')
    new_name = simpledialog.askstring("Modify Student", "Enter new name:")
    if new_name is None or new_name.strip() == "":
        return
    new_prn = simpledialog.askstring("Modify Student", "Enter new PRN:")
    if new_prn is None or new_prn.strip() == "":
        return
    if update_student(old_prn, new_name.strip(), new_prn.strip()):
        messagebox.showinfo("Success", "Student updated successfully.")
        refresh_student_list()
    else:
        messagebox.showerror("Error", "PRN already exists or update failed.")

# Tkinter GUI setup
root = tk.Tk()
root.title("Attendance Management")
root.geometry("600x400")
root.configure(bg="#f0f0f0")

frame = tk.Frame(root, bg="#f0f0f0")
frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

student_listbox = tk.Listbox(frame, width=40, height=10, font=("Helvetica", 12))
student_listbox.grid(row=0, column=0, columnspan=3, pady=10, sticky="nsew")

tk.Label(frame, text="Name:", bg="#f0f0f0", font=("Helvetica", 12)).grid(row=1, column=0, sticky=tk.E, pady=5)
name_entry = tk.Entry(frame, font=("Helvetica", 12))
name_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W+tk.E, pady=5)

tk.Label(frame, text="PRN:", bg="#f0f0f0", font=("Helvetica", 12)).grid(row=2, column=0, sticky=tk.E, pady=5)
prn_entry = tk.Entry(frame, font=("Helvetica", 12))
prn_entry.grid(row=2, column=1, columnspan=2, sticky=tk.W+tk.E, pady=5)

add_button = tk.Button(frame, text="Add Student", command=add_student_gui, bg="#4CAF50", fg="white", font=("Helvetica", 12), relief=tk.FLAT)
add_button.grid(row=3, column=0, pady=10, sticky="ew")

remove_button = tk.Button(frame, text="Remove Student", command=remove_student_gui, bg="#f44336", fg="white", font=("Helvetica", 12), relief=tk.FLAT)
remove_button.grid(row=3, column=1, pady=10, sticky="ew")

modify_button = tk.Button(frame, text="Modify Student", command=modify_student_gui, bg="#2196F3", fg="white", font=("Helvetica", 12), relief=tk.FLAT)
modify_button.grid(row=3, column=2, pady=10, sticky="ew")

start_button = tk.Button(root, text="Start Video Attendance", command=start_video_attendance, bg="#FF9800", fg="white", font=("Helvetica", 14), relief=tk.FLAT)
start_button.grid(row=1, column=0, pady=15, sticky="ew", padx=20)

# New button for exporting attendance by date
def export_attendance_by_date():
    date_str = simpledialog.askstring("Export Attendance", "Enter date (YYYY-MM-DD):")
    if not date_str:
        return
    try:
        # Validate date format
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
        return

    records = get_attendance_by_date(date_str)
    if not records:
        messagebox.showinfo("No Records", f"No attendance records found for {date_str}.")
        return

    # Prepare data for DataFrame
    data = [{"Name": r[0], "Status": r[1], "Timestamp": r[2]} for r in records]
    df = pd.DataFrame(data)

    # Ask user where to save the Excel file
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel files", "*.xlsx")],
                                             initialfile=f"attendance_{date_str}.xlsx")
    if not file_path:
        return

    try:
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Success", f"Attendance exported successfully to {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save Excel file: {e}")

export_button = tk.Button(root, text="Export Attendance by Date", command=export_attendance_by_date, bg="#9C27B0", fg="white", font=("Helvetica", 14), relief=tk.FLAT)
export_button.grid(row=2, column=0, pady=15, sticky="ew", padx=20)

root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=0)
root.grid_rowconfigure(2, weight=0)
root.grid_columnconfigure(0, weight=1)

frame.grid_columnconfigure(1, weight=1)
frame.grid_columnconfigure(2, weight=1)
frame.grid_rowconfigure(0, weight=1)

refresh_student_list()

root.mainloop()
