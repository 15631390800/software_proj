from flask import Flask, request, render_template
import sqlite3

app = Flask(__name__)

# 数据库初始化
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

if __name__ == '__main__':
    app.run(debug=True)
