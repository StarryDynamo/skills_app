import sqlite3

DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.close()

import sqlite3

DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.close()

def populate_db():
    roles = [
        ('L&D Manager',),
        ('L&D Specialist',),
        ('Instructional Designer',),
        ('Training Coordinator',)
    ]

    skills = [
        (1, 'Instructional Design', 5),
        (1, 'Project Management', 5),
        (1, 'Leadership', 4),
        (1, 'Coaching', 4),
        (2, 'Curriculum Development', 5),
        (2, 'E-learning Development', 4),
        (2, 'Needs Analysis', 4),
        (2, 'Training Delivery', 5),
        (3, 'Content Development', 5),
        (3, 'Storyboarding', 4),
        (3, 'Graphic Design', 3),
        (3, 'Multimedia Production', 3),
        (4, 'Event Planning', 5),
        (4, 'Scheduling', 4),
        (4, 'Communication', 4),
        (4, 'Administration', 3)
    ]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.executemany('INSERT INTO roles (name) VALUES (?)', roles)
    cursor.executemany('INSERT INTO skills (role_id, name, required_level) VALUES (?, ?, ?)', skills)

    conn.commit()
    conn.close()

# Initialize and populate the database
init_db()
populate_db()

