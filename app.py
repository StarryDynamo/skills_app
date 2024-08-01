from flask import Flask, request, render_template, redirect, url_for
import sqlite3
from dotenv import load_dotenv
import os
from openai import OpenAI

app = Flask(__name__)

DATABASE = 'database.db'
REQUIRED_LEVEL = 4  # Set the required level for all tasks

# Load env variables from the .env file
load_dotenv()

# Set up OpenAI API Key
client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY')
)

if client.api_key is None:
    raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_learning_recommendations(gaps):
    content = "Based on the following skill gaps, recommend a learning pathway based on the learning theory of Connectivism, do not mention the theory in the output, simply base your design on the theory. Ensure all sources you link to are reputable: "
    for task, (level, required_level) in gaps.items():
        content += f"\n- Task: {task}, Current Level: {level}, Required Level: {required_level}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that provides learning recommendations."},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "There was an issue generating recommendations. Please try again later."

@app.route('/')
def index():
    conn = get_db()
    roles = conn.execute('SELECT * FROM roles').fetchall()
    conn.close()
    return render_template('index.html', roles=roles)

@app.route('/role')
def role():
    role_id = request.args.get('role_id')
    conn = get_db()
    role = conn.execute('SELECT * FROM roles WHERE id = ?', (role_id,)).fetchone()
    tasks = conn.execute('SELECT * FROM tasks WHERE role_id = ?', (role_id,)).fetchall()
    conn.close()
    return render_template('role.html', role=role, tasks=tasks)

@app.route('/assess', methods=['POST'])
def assess():
    role_id = request.form['role_id']
    user_name = request.form['user_name']
    task_ids = request.form.getlist('task_id')
    levels = request.form.getlist('level')

    conn = get_db()

    # Fetch or create user
    user = conn.execute('SELECT * FROM users WHERE name = ?', (user_name,)).fetchone()
    if not user:
        conn.execute('INSERT INTO users (name) VALUES (?)', (user_name,))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE name = ?', (user_name,)).fetchone()
    user_id = user['id']

    # Insert assessments
    for task_id, level in zip(task_ids, levels):
        conn.execute('INSERT INTO assessments (user_id, task_id, level) VALUES (?, ?, ?)',
                     (user_id, task_id, level))

    conn.commit()
    conn.close()

    return redirect(url_for('results', user_id=user_id, role_id=role_id))

@app.route('/results/<int:user_id>/<int:role_id>')
def results(user_id, role_id):
    conn = get_db()
    role = conn.execute('SELECT * FROM roles WHERE id = ?', (role_id,)).fetchone()
    tasks = conn.execute('''
        SELECT t.task_name, a.level
        FROM tasks t
        LEFT JOIN assessments a ON t.id = a.task_id AND a.user_id = ?
        WHERE t.role_id = ?
    ''', (user_id, role_id)).fetchall()

    strengths = {}
    gaps = {}

    for task in tasks:
        task_name, level = task['task_name'], task['level']
        if level is None:
            level = 0
        if level >= REQUIRED_LEVEL:
            strengths[task_name] = level
        else:
            gaps[task_name] = (level, REQUIRED_LEVEL)

    learning_recommendations = get_learning_recommendations(gaps)

    conn.close()
    return render_template('results.html', role=role, strengths=strengths, gaps=gaps, learning_recommendations=learning_recommendations)

@app.route('/manager')
def manager():
    conn = get_db()
    users = conn.execute('SELECT id, name FROM users').fetchall()
    tasks = conn.execute('SELECT id, task_name FROM tasks').fetchall()
    conn.close()
    return render_template('manager.html', users=users, tasks=tasks)

@app.route('/manager/search', methods=['POST'])
def manager_search():
    user_id = request.form['user_id']
    return redirect(url_for('manager_user', user_id=user_id))

@app.route('/manager/task_search', methods=['POST'])
def manager_task_search():
    task_id = request.form['task_id']

    conn = get_db()
    users = conn.execute('''
        SELECT u.name, a.level
        FROM users u
        JOIN assessments a ON u.id = a.user_id
        WHERE a.task_id = ? AND a.level IS NOT NULL
    ''', (task_id,)).fetchall()
    task = conn.execute('SELECT task_name FROM tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()
    return render_template('manager_task_results.html', users=users, task_name=task['task_name'])

@app.route('/manager/user/<int:user_id>')
def manager_user(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    assessments = conn.execute('''
        SELECT r.name as role_name, t.task_name, a.level
        FROM assessments a
        JOIN tasks t ON a.task_id = t.id
        JOIN roles r ON t.role_id = r.id
        WHERE a.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('manager_user.html', user=user, assessments=assessments)

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    conn = get_db()
    if request.method == 'POST':
        user_name = request.form['user_name']
        role_id = request.form['role_id']
        task_name = request.form['task_name']
        frequency = request.form['frequency']

        user = conn.execute('SELECT * FROM users WHERE name = ?', (user_name,)).fetchone()
        if not user:
            conn.execute('INSERT INTO users (name) VALUES (?)', (user_name,))
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE name = ?', (user_name,)).fetchone()
        user_id = user['id']

        conn.execute('INSERT INTO tasks (user_id, role_id, task_name, frequency) VALUES (?, ?, ?, ?)',
                     (user_id, role_id, task_name, frequency))
        conn.commit()

    roles = conn.execute('SELECT id, name FROM roles').fetchall()
    tasks = conn.execute('''
        SELECT u.name as user_name, r.name as role_name, t.task_name, t.frequency
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        JOIN roles r ON t.role_id = r.id
    ''').fetchall()

    conn.close()
    return render_template('tasks.html', roles=roles, tasks=tasks)

if __name__ == '__main__':
    app.run(debug=True)
