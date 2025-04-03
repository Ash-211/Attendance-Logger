import sqlite3

def connect_db():
    conn = sqlite3.connect('attendance.db')
    return conn

def create_tables():
    """Create the attendance and images tables if they don't exist."""
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
    
    conn.commit()
    conn.close()

def insert_attendance(name, status):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO attendance (name, status) VALUES (?, ?)
    ''', (name, status))
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