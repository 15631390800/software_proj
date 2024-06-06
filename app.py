from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_db():
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            options TEXT,
            answer TEXT NOT NULL,
            difficulty INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_questions (
            exam_id INTEGER,
            question_id INTEGER,
            FOREIGN KEY (exam_id) REFERENCES exams(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_answers (
            student_id INTEGER,
            exam_id INTEGER,
            question_id INTEGER,
            answer TEXT,
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (exam_id) REFERENCES exams(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def add_question(q_type, content, options, answer, difficulty):
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO questions (type, content, options, answer, difficulty)
        VALUES (?, ?, ?, ?, ?)
    ''', (q_type, content, options, answer, difficulty))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'role' in session and session['role'] == 'teacher':
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password)
        
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, role))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return 'Username already exists!'
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password, role FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['role'] = user[2]
            if user[2] == 'teacher':
                return redirect(url_for('index'))
            elif user[2] == 'student':
                return redirect(url_for('student_home'))
        return 'Invalid username or password!'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/add_question_form')
def add_question_form():
    if 'role' in session and session['role'] == 'teacher':
        return render_template('add_question_form.html')
    return redirect(url_for('login'))

@app.route('/add_question', methods=['POST'])
def add_question_route():
    if 'role' in session and session['role'] == 'teacher':
        q_type = request.form['type']
        content = request.form['content']
        options = request.form['options']
        answer = request.form['answer']
        difficulty = int(request.form['difficulty'])
        add_question(q_type, content, options, answer, difficulty)
        return 'Question added successfully!'
    return redirect(url_for('login'))

@app.route('/view_questions')
def view_questions():
    if 'role' in session and session['role'] == 'teacher':
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM questions')
        questions = cursor.fetchall()
        conn.close()
        return render_template('view_questions.html', questions=questions)
    return redirect(url_for('login'))

@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
    if 'role' in session and session['role'] == 'teacher':
        if request.method == 'POST':
            exam_name = request.form['exam_name']
            conn = sqlite3.connect('exam_database.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO exams (name) VALUES (?)', (exam_name,))
            conn.commit()
            exam_id = cursor.lastrowid
            conn.close()
            return redirect(url_for('select_questions', exam_id=exam_id))
        return render_template('create_exam.html')
    return redirect(url_for('login'))

@app.route('/select_questions/<int:exam_id>', methods=['GET', 'POST'])
def select_questions(exam_id):
    if 'role' in session and session['role'] == 'teacher':
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        if request.method == 'POST':
            question_id = int(request.form['question_id'])
            cursor.execute('SELECT * FROM exam_questions WHERE exam_id=? AND question_id=?', (exam_id, question_id))
            if cursor.fetchone() is None:
                cursor.execute('INSERT INTO exam_questions (exam_id, question_id) VALUES (?, ?)', (exam_id, question_id))
                conn.commit()
        cursor.execute('SELECT * FROM questions')
        questions = cursor.fetchall()
        cursor.execute('SELECT q.id, q.type, q.content, q.options, q.answer, q.difficulty FROM questions q JOIN exam_questions eq ON q.id = eq.question_id WHERE eq.exam_id=?', (exam_id,))
        selected_questions = cursor.fetchall()
        conn.close()
        return render_template('select_questions.html', questions=questions, selected_questions=selected_questions, exam_id=exam_id)
    return redirect(url_for('login'))

@app.route('/view_exam/<int:exam_id>')
def view_exam(exam_id):
    if 'role' in session and session['role'] == 'teacher':
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM exams WHERE id=?', (exam_id,))
        exam = cursor.fetchone()
        cursor.execute('SELECT q.id, q.type, q.content, q.options, q.answer, q.difficulty FROM questions q JOIN exam_questions eq ON q.id = eq.question_id WHERE eq.exam_id=?', (exam_id,))
        questions = cursor.fetchall()
        conn.close()
        return render_template('view_exam.html', exam=exam, questions=questions)
    return redirect(url_for('login'))

@app.route('/student_home')
def student_home():
    if 'role' in session and session['role'] == 'student':
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM exams')
        exams = cursor.fetchall()
        conn.close()
        return render_template('student_home.html', username=session['username'], exams=exams)
    return redirect(url_for('login'))

@app.route('/take_exam/<int:exam_id>', methods=['GET', 'POST'])
def take_exam(exam_id):
    if 'role' in session and session['role'] == 'student':
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM exams WHERE id=?', (exam_id,))
        exam_name = cursor.fetchone()[0]
        cursor.execute('''
            SELECT q.id, q.type, q.content, q.options, q.answer, q.difficulty 
            FROM questions q 
            JOIN exam_questions eq ON q.id = eq.question_id 
            WHERE eq.exam_id=?
        ''', (exam_id,))
        questions = cursor.fetchall()
        conn.close()
        return render_template('take_exam.html', exam_id=exam_id, exam_name=exam_name, questions=questions)
    return redirect(url_for('login'))

@app.route('/submit_exam/<int:exam_id>', methods=['POST'])
def submit_exam(exam_id):
    if 'role' in session and session['role'] == 'student':
        student_id = session['user_id']
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        for key, value in request.form.items():
            question_id = int(key.split('_')[1])
            answer = value
            cursor.execute('''
                INSERT INTO student_answers (student_id, exam_id, question_id, answer)
                VALUES (?, ?, ?, ?)
            ''', (student_id, exam_id, question_id, answer))
        conn.commit()
        conn.close()
        return 'Exam submitted successfully!'
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
