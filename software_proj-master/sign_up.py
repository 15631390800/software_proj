from flask import Flask, request, render_template, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 现有的 init_db 函数

# 注册用户
def register_user(username, password, user_type):
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute('''
            INSERT INTO users (username, password, user_type)
            VALUES (?, ?, ?)
        ''', (username, hashed_password, user_type))
        conn.commit()
    except sqlite3.IntegrityError:
        flash('Username already exists')
        return False
    finally:
        conn.close()
    return True

# 验证用户
def validate_user(username, password):
    conn = sqlite3.connect('exam_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=?', (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user[2], password):
        return user
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        if register_user(username, password, user_type):
            flash('Registration successful')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = validate_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['user_type'] = user[3]
            if user[3] == 'teacher':
                return redirect(url_for('index'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 学生仪表盘
@app.route('/student_dashboard')
def student_dashboard():
    return 'Welcome to the student dashboard!'

# 现有的路由

if __name__ == '__main__':
    app.run(debug=True)
