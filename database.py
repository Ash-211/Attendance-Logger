import sqlite3

def connect_db():
    conn = sqlite3.connect('attendance.db')
    return conn

def create_tables():
    """Create the attendance, images, and students tables if they don't exist."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image BLOB NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            prn TEXT UNIQUE NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

from datetime import datetime, timedelta

def insert_attendance(name, status):
    conn = connect_db()
    cursor = conn.cursor()
    from datetime import datetime, timedelta
    # Calculate current IST date string
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_ist_date = ist_now.strftime('%Y-%m-%d')
    timestamp_str = ist_now.strftime('%Y-%m-%d %H:%M:%S')
    # Check if attendance for this student already exists for current IST date
    cursor.execute('''
        SELECT id, status FROM attendance
        WHERE name = ? AND DATE(timestamp) = ?
    ''', (name, current_ist_date))
    existing = cursor.fetchone()
    if existing:
        existing_id, existing_status = existing
        if existing_status == 'Absent' and status == 'Present':
            # Update record to Present with new timestamp
            cursor.execute('''
                UPDATE attendance SET status = ?, timestamp = ? WHERE id = ?
            ''', (status, timestamp_str, existing_id))
            conn.commit()
        # If already Present, do nothing
        conn.close()
        return
    # Insert new attendance record
    cursor.execute('''
        INSERT INTO attendance (name, status, timestamp) VALUES (?, ?, ?)
    ''', (name, status, timestamp_str))
    conn.commit()
    conn.close()

def insert_image(name, image):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO images (name, image) VALUES (?, ?)
    ''', (name, image))
    conn.commit()
    conn.close()

def add_student(name, prn):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO students (name, prn) VALUES (?, ?)
        ''', (name, prn))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def remove_student(prn):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM students WHERE prn = ?
    ''', (prn,))
    conn.commit()
    conn.close()

def update_student(prn, new_name, new_prn):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE students SET name = ?, prn = ? WHERE prn = ?
        ''', (new_name, new_prn, prn))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def get_all_students():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT name, prn FROM students ORDER BY name')
    students = cursor.fetchall()
    conn.close()
    return students

def get_attendance_by_date(date_str):
    """
    Fetch attendance records for a specific date.
    date_str should be in 'YYYY-MM-DD' format.
    """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, status, timestamp FROM attendance
        WHERE DATE(timestamp) = ?
        ORDER BY timestamp
    ''', (date_str,))
    records = cursor.fetchall()
    conn.close()
    return records
