from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
import json
import csv
import io

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
            difficulty INTEGER NOT NULL,
            teacher TEXT NOT NULL
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

def add_question(q_type, content, options, answer, difficulty, user_name):
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO questions (type, content, options, answer, difficulty, teacher)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (q_type, content, options, answer, difficulty, user_name))
    conn.commit()
    conn.close()

def delete_question(question_id):
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        cursor.execute('DELETE FROM questions WHERE id = ?
        VALUES (?)
    ''', (question_id))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
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
            elif user[2] == 'administrator':
                return redirect(url_for('index'))
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
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
        return render_template('add_question_form.html')
    return redirect(url_for('login'))

@app.route('/add_question', methods=['GET', 'POST'])
def add_question_route():
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
        if request.method == 'POST':
            q_type = request.form['q_type']  # 使用新的q_type字段
            content = request.form['content']
            options = request.form['options']
            answer = request.form['answer']
            difficulty = int(request.form['difficulty'])
            username = session['username']
            add_question(q_type, content, options, answer, difficulty, username)
            return render_template('add_question_form.html')
        else:
            return render_template('add_question_form.html')
    else:
        return "Unauthorized", 403

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    excel_data = request.form.get('excel_data')
    if not excel_data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    
    questions = json.loads(excel_data)
    
    for question in questions:
        # 处理每个问题的添加逻辑
        q_type = question.get('Question Type')
        content = question.get('Content')
        options = question.get('Options')
        answer = question.get('Answer')
        difficulty = question.get('Difficulty')
        username = session['username']
        add_question(q_type, content, options, answer, difficulty, username)
        # 添加到数据库的逻辑
        # ...
    
    return render_template('add_question_form.html')

# 每页显示的题目数量
PER_PAGE = 10

@app.route('/view_questions')
@app.route('/view_questions/<int:page>')
def view_questions(page=1):
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
        conn = None
        try:
            conn = sqlite3.connect('exam_database.db')
            cursor = conn.cursor()

            # 查询总题目数量
            cursor.execute('SELECT COUNT(*) FROM questions')
            total_questions = cursor.fetchone()[0]
            print(total_questions)
            # 计算总页数
            total_pages = (total_questions + PER_PAGE - 1) // PER_PAGE
            print(total_pages)
            # 计算偏移量
            offset = (page - 1) * PER_PAGE

            # cursor.execute('SELECT role FROM users WHERE username=?', (session['username']))

            # 查询当前页面的题目
            cursor.execute('SELECT * FROM questions LIMIT ? OFFSET ?', (PER_PAGE, offset))
            questions = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            questions = []
        except Exception as e:
            print(f"General error: {e}")
            questions = []
        finally:
            if conn:
                conn.close()

        return render_template('view_questions.html', questions=questions, page=page, total_pages=total_pages, current_username=str(session['username']), role=str(session['role']))
    return redirect(url_for('login'))

@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if 'role' in session:
        conn = None
        try:
            conn = sqlite3.connect('exam_database.db')
            cursor = conn.cursor()

            if session['role'] == 'teacher':
                # 检查题目是否属于当前用户
                cursor.execute('SELECT COUNT(*) FROM questions WHERE id = ? AND teacher = ?', (question_id, session['username']))
                if cursor.fetchone()[0] == 0:
                    flash('You do not have permission to delete this question.')
                    return redirect(url_for('view_questions'))

                # 删除题目
                cursor.execute('DELETE FROM questions WHERE id = ? AND teacher = ?', (question_id, session['username']))
            elif session['role'] == 'administrator':
                # 管理员可以直接删除任何题目
                cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))

            conn.commit()
            flash('Question deleted successfully.')
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            flash('Failed to delete question due to a database error.')
        except Exception as e:
            print(f"General error: {e}")
            flash('Failed to delete question due to a general error.')
        finally:
            if conn:
                conn.close()

        return redirect(url_for('view_questions'))
    
    return redirect(url_for('login'))




@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
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
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
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
        
        # 统计题目类型和难易值
        type_count = {}
        difficulty_count = {}
        for q in selected_questions:
            q_type = q[1]
            difficulty = q[5]
            type_count[q_type] = type_count.get(q_type, 0) + 1
            difficulty_count[difficulty] = difficulty_count.get(difficulty, 0) + 1
        
        conn.close()
        return render_template('select_questions.html', questions=questions, selected_questions=selected_questions, exam_id=exam_id, type_count=type_count, difficulty_count=difficulty_count)
    return redirect(url_for('login'))


@app.route('/view_exam/<int:exam_id>')
def view_exam(exam_id):
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
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
        student_answers = []
        for key, value in request.form.items():
            question_id = int(key.split('_')[1])
            answer = value
            cursor.execute('''
                INSERT INTO student_answers (student_id, exam_id, question_id, answer)
                VALUES (?, ?, ?, ?)
            ''', (student_id, exam_id, question_id, answer))
            student_answers.append((question_id, answer))

        # 查询正确答案
        correct_answers = {}
        cursor.execute('SELECT id, answer FROM questions WHERE id IN ({})'.format(','.join(str(qid) for qid, _ in student_answers)))
        for row in cursor.fetchall():
            correct_answers[row[0]] = row[1]

        # 查询题目内容和选项
        question_details = {}
        cursor.execute('SELECT id, content, options FROM questions WHERE id IN ({})'.format(','.join(str(qid) for qid, _ in student_answers)))
        for row in cursor.fetchall():
            question_id = row[0]
            content = row[1]
            options = row[2]
            question_details[question_id] = {'content': content, 'options': options, 'answer': '', 'correct_answer': '', 'question_type': '', 'is_correct': False}

        # 查询题目类型
        cursor.execute('SELECT id, type FROM questions WHERE id IN ({})'.format(','.join(str(qid) for qid, _ in student_answers)))
        for row in cursor.fetchall():
            question_id = row[0]
            question_type = row[1]
            if question_id in question_details:
                question_details[question_id]['question_type'] = question_type

        # 添加学生答案和正确答案到 question_details
        for question_id, answer in student_answers:
            if question_id in question_details:
                question_details[question_id]['answer'] = answer
                question_details[question_id]['correct_answer'] = correct_answers.get(question_id, 'Not available')
                question_details[question_id]['is_correct'] = answer == correct_answers.get(question_id, '')

        conn.commit()
        conn.close()

        return render_template('exam_report.html', question_details=question_details)


@app.route('/select_exam', methods=['GET', 'POST'])
def select_exam():
    if request.method == 'POST':
        exam_name = request.form['exam_name']
        
        # 查找考试ID
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM exams WHERE name = ?', (exam_name,))
        exam = cursor.fetchone()
        conn.close()
        
        if exam:
            exam_id = exam[0]
            return redirect(url_for('view_grades', exam_id=exam_id))
        else:
            return "Exam not found"
    
    # 如果是GET请求，返回表单页面
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM exams')
    exams = cursor.fetchall()
    conn.close()
    
    # 将 exams 转换为字典列表
    exams = [{'id': exam[0], 'name': exam[1]} for exam in exams]
    
    return render_template('select_exam.html', exams=exams)

@app.route('/view_grades/<int:exam_id>')
def view_grades(exam_id):
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        
        # Fetch exam name
        cursor.execute('SELECT name FROM exams WHERE id = ?', (exam_id,))
        exam_name = cursor.fetchone()[0]  # Assuming 'name' is the column name for exam name
        
        # Fetch student grades
        cursor.execute('''
            SELECT users.username, student_answers.student_id, student_answers.answer, questions.answer, questions.content
            FROM student_answers
            JOIN users ON student_answers.student_id = users.id
            JOIN questions ON student_answers.question_id = questions.id
            WHERE student_answers.exam_id = ?
        ''', (exam_id,))
        grades = cursor.fetchall()
        conn.close()
        
        student_scores = {}
        for row in grades:
            student_name = row[0]
            student_id = row[1]
            student_answer = row[2]
            correct_answer = row[3]
            question_content = row[4]
            if student_id not in student_scores:
                student_scores[student_id] = {'name': student_name, 'correct': 0, 'total': 0}
            student_scores[student_id]['total'] += 1
            if student_answer == correct_answer:
                student_scores[student_id]['correct'] += 1

        scores = [score['correct'] / score['total'] * 100 for score in student_scores.values()]
        average_score = sum(scores) / len(scores) if scores else 0
        highest_score = max(scores, default=0)
        lowest_score = min(scores, default=0)

        return render_template('view_grades.html', student_scores=student_scores.values(), exam_name=exam_name,
                               average_score=average_score, highest_score=highest_score, lowest_score=lowest_score,
                               exam_id=exam_id)
    return redirect(url_for('login'))

@app.route('/export_grades/<int:exam_id>')
def export_grades(exam_id):
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
        conn = sqlite3.connect('exam_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT users.username, student_answers.student_id, student_answers.answer, questions.answer, questions.content
            FROM student_answers
            JOIN users ON student_answers.student_id = users.id
            JOIN questions ON student_answers.question_id = questions.id
            WHERE student_answers.exam_id = ?
        ''', (exam_id,))
        grades = cursor.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Student Name', 'Student ID', 'Student Answer', 'Correct Answer' ,'Question Content'])
        
        for row in grades:
            writer.writerow(row)

        output.seek(0)
        byte_output = io.BytesIO()
        byte_output.write(output.getvalue().encode('utf-8'))
        byte_output.seek(0)
        return send_file(byte_output, mimetype='text/csv', download_name='grades.csv', as_attachment=True)
    return redirect(url_for('login'))

def generate_random_exam(num_questions, difficulty_levels, question_types):
    with sqlite3.connect('exam_database.db') as conn:
        cursor = conn.cursor()
        
        selected_questions = []
        
        # 获取符合条件的所有题目
        query = 'SELECT id, type, difficulty FROM questions WHERE difficulty IN ({}) AND type IN ({})'.format(
            ','.join('?' for _ in difficulty_levels),
            ','.join('?' for _ in question_types)
        )
        cursor.execute(query, difficulty_levels + question_types)
        questions = cursor.fetchall()
        
        # 按类型和难度分类题目
        categorized_questions = {}
        for question in questions:
            q_id, q_type, q_difficulty = question
            q_difficulty = str(q_difficulty)  # 确保q_difficulty作为字符串使用
            if q_type not in categorized_questions:
                categorized_questions[q_type] = {}
            if q_difficulty not in categorized_questions[q_type]:
                categorized_questions[q_type][q_difficulty] = []
            categorized_questions[q_type][q_difficulty].append(q_id)
        
        # 按类型和难度随机选题
        total_selected = 0
        for q_type in question_types:
            for q_difficulty in difficulty_levels: 
                q_difficulty = str(q_difficulty)  # 确保使用一致的数据类型
                if (q_type in categorized_questions and 
                    q_difficulty in categorized_questions[q_type] and 
                    isinstance(categorized_questions[q_type][q_difficulty], list)):
                    
                    available_questions = categorized_questions[q_type][q_difficulty]
                    
                    num_to_select = min(num_questions // len(question_types) // len(difficulty_levels), len(available_questions))
                    total_selected += num_to_select
                    
                    try:
                        question_to_select = random.sample(available_questions, num_to_select)
                        selected_questions.extend(question_to_select)
                        for q_id in question_to_select:
                            categorized_questions[q_type][q_difficulty].remove(q_id)
                    except ValueError as e:
                        print(f"Error selecting questions: {e}")
        
        if total_selected < num_questions:
            remaining_questions = num_questions - total_selected
            additional_questions = []
            for q_type in question_types:
                for q_difficulty in difficulty_levels: 
                    q_difficulty = str(q_difficulty)  # 确保使用一致的数据类型
                    if (q_type in categorized_questions and 
                        q_difficulty in categorized_questions[q_type] and 
                        isinstance(categorized_questions[q_type][q_difficulty], list)):
                        
                        additional_questions.extend(categorized_questions[q_type][q_difficulty])
            
            if len(additional_questions) >= remaining_questions:
                selected_questions.extend(random.sample(additional_questions, remaining_questions))
            else:
                selected_questions.extend(additional_questions)
        
        return selected_questions

@app.route('/generate_exam', methods=['GET', 'POST'])
def generate_exam():
    if 'role' in session and session['role'] in ['teacher' , 'administrator']:
        if request.method == 'POST':
            exam_name = request.form['exam_name']
            num_questions = int(request.form['num_questions'])
            difficulty_levels = request.form.getlist('difficulty_levels')
            question_types = request.form.getlist('question_types')
            
            selected_questions = generate_random_exam(num_questions, difficulty_levels, question_types)
            
            conn = sqlite3.connect('exam_database.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO exams (name) VALUES (?)', (exam_name,))
            exam_id = cursor.lastrowid
            
            for question_id in selected_questions:
                cursor.execute('INSERT INTO exam_questions (exam_id, question_id) VALUES (?, ?)', (exam_id, question_id))
            
            conn.commit()
            conn.close()
            
            return redirect(url_for('view_exam', exam_id=exam_id))
        
        return render_template('generate_exam.html')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
