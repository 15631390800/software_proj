import sqlite3

# 连接到数据库
conn = sqlite3.connect('exam_database.db')

# 创建一个游标对象
cursor = conn.cursor()

# SQL语句删除id为6的记录
sql_delete_query = """DELETE FROM users WHERE id = 6"""

try:
    # 执行SQL语句
    cursor.execute(sql_delete_query)
    # 提交更改
    conn.commit()
    print("删除成功")
except sqlite3.Error as error:
    print(f"删除数据时发生错误: {error}")
finally:
    # 关闭连接
    if conn:
        conn.close()
