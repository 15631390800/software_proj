import sqlite3

# 连接到SQLite数据库（如果数据库不存在，则会自动创建）
conn = sqlite3.connect('exam_database.db')
cursor = conn.cursor()

# 创建题目表，包含题目类型、内容、答案、难易度等字段
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

def add_question(q_type, content, options, answer, difficulty):
    cursor.execute('''
        INSERT INTO questions (type, content, options, answer, difficulty)
        VALUES (?, ?, ?, ?, ?)
    ''', (q_type, content, options, answer, difficulty))
    conn.commit()

def add_single_choice(content, options, answer, difficulty):
    add_question('single_choice', content, options, answer, difficulty)

def add_multiple_choice(content, options, answer, difficulty):
    add_question('multiple_choice', content, options, answer, difficulty)

def add_true_false(content, answer, difficulty):
    add_question('true_false', content, None, answer, difficulty)

def add_short_answer(content, answer, difficulty):
    add_question('short_answer', content, None, answer, difficulty)

# 示例：添加不同类型的题目
add_single_choice(
    content="What is the capital of France?",
    options="A) Paris, B) London, C) Berlin, D) Madrid",
    answer="A",
    difficulty=1
)

add_multiple_choice(
    content="Which of the following are programming languages?",
    options="A) Python, B) HTML, C) JavaScript, D) CSS",
    answer="A,C",
    difficulty=2
)

add_true_false(
    content="The Earth is flat.",
    answer="False",
    difficulty=1
)

add_short_answer(
    content="Describe the process of photosynthesis.",
    answer="Photosynthesis is the process by which green plants use sunlight to synthesize foods from carbon dioxide and water.",
    difficulty=3
)

# 查询所有题目
cursor.execute('SELECT * FROM questions')
all_questions = cursor.fetchall()
for question in all_questions:
    print(question)

# 关闭数据库连接
conn.close()
