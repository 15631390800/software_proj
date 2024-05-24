from flask import Flask, request, render_template, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
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
    return render_template('index.html')

@app.route('/add_question_form')
def add_question_form():
    return render_template('add_question_form.html')

@app.route('/add_question', methods=['POST'])
def add_question_route():
    q_type = request.form['type']
    content = request.form['content']
    options = request.form['options']
    answer = request.form['answer']
    difficulty = int(request.form['difficulty'])
    add_question(q_type, content, options, answer, difficulty)
    return 'Question added successfully!'

@app.route('/view_questions')
def view_questions():
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM questions')
    questions = cursor.fetchall()
    conn.close()
    return render_template('view_questions.html', questions=questions)

@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
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

@app.route('/select_questions/<int:exam_id>', methods=['GET', 'POST'])
def select_questions(exam_id):
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

@app.route('/view_exam/<int:exam_id>')
def view_exam(exam_id):
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM exams WHERE id=?', (exam_id,))
    exam = cursor.fetchone()
    cursor.execute('SELECT q.id, q.type, q.content, q.options, q.answer, q.difficulty FROM questions q JOIN exam_questions eq ON q.id = eq.question_id WHERE eq.exam_id=?', (exam_id,))
    questions = cursor.fetchall()
    conn.close()
    return render_template('view_exam.html', exam=exam, questions=questions)

if __name__ == '__main__':
    app.run(debug=True)
