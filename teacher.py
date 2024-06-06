from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'teacher':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    if session.get('user_type') == 'teacher':
        return render_template('index.html')
    else:
        return redirect(url_for('student_dashboard'))

# 现有的路由都需要保护
@app.route('/add_question_form')
@teacher_required
def add_question_form():
    return render_template('add_question_form.html')

# ... 其他需要保护的路由

if __name__ == '__main__':
    app.run(debug=True)
