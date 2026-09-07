from flask import Flask, request, jsonify, render_template, session
import sqlite3
import os
import subprocess

app = Flask(__name__)
app.secret_key = 'robust_v5_5_secret_key'

# กำหนด Path ของฐานข้อมูลให้ชี้ไปที่โฟลเดอร์บน PythonAnywhere โดยตรง
DB_PATH = '/home/panusddn/mysite/database.db'

def get_db_connection():
    # ฟังก์ชันตัวช่วยสำหรับเชื่อมต่อฐานข้อมูล
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  level INTEGER, 
                  score INTEGER)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # เริ่มต้นที่ด่าน 0 และคะแนน 100
        c.execute("INSERT INTO users (username, password, level, score) VALUES (?, ?, 0, 100)", 
                  (data['username'], data['password']))
        conn.commit()
        return jsonify({'success': True, 'message': 'สมัครสมาชิกสำเร็จ โปรดเข้าสู่ระบบ'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'ชื่อผู้ใช้นี้มีในระบบแล้ว'})
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, level, score FROM users WHERE username=? AND password=?", 
              (data['username'], data['password']))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user[0]
        session['username'] = data['username']
        return jsonify({'success': True, 'level': user[1], 'score': user[2], 'username': data['username']})
    return jsonify({'success': False, 'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'})

@app.route('/save', methods=['POST'])
def save():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'กรุณาเข้าสู่ระบบ'})
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET level=?, score=? WHERE id=?", 
              (data['level'], data['score'], session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/webhook', methods=['POST'])
def webhook():
    # ดึงโค้ดล่าสุดจาก GitHub
    subprocess.run(['git', 'pull', 'origin', 'main'], cwd='/home/panusddn/mysite')
    # สั่งรีสตาร์ทเซิร์ฟเวอร์อัตโนมัติ
    subprocess.run(['touch', '/var/www/panusddn_pythonanywhere_com_wsgi.py'])
    return "Updated successfully", 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
