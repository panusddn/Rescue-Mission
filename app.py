from flask import Flask, request, jsonify, render_template, session
import sqlite3
import time
import os
import subprocess

app = Flask(__name__)
app.secret_key = 'robust_v5_5_secret_key'

DB_PATH = '/home/panusddn/mysite/database.db'

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  level INTEGER, 
                  score INTEGER)''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN last_seen REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
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
        c.execute("INSERT INTO users (username, password, level, score, last_seen) VALUES (?, ?, 0, 100, ?)", 
                  (data['username'], data['password'], time.time()))
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
    if user:
        session['user_id'] = user[0]
        session['username'] = data['username']
        c.execute("UPDATE users SET last_seen=? WHERE id=?", (time.time(), user[0]))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'level': user[1], 'score': user[2], 'username': data['username']})
    conn.close()
    return jsonify({'success': False, 'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'})

@app.route('/save', methods=['POST'])
def save():
    if 'user_id' not in session:
        return jsonify({'success': False})
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET level=?, score=?, last_seen=? WHERE id=?", 
              (data['level'], data['score'], time.time(), session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

# --- ระบบ Online Users ---
@app.route('/ping', methods=['POST'])
def ping():
    if 'user_id' in session:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET last_seen=? WHERE id=?", (time.time(), session['user_id']))
        conn.commit()
        conn.close()
    return jsonify({'success': True})

@app.route('/online_users', methods=['GET'])
def online_users():
    conn = get_db_connection()
    c = conn.cursor()
    active_threshold = time.time() - 120 
    c.execute("SELECT username, level, score FROM users WHERE last_seen > ? ORDER BY score DESC, level DESC", (active_threshold,))
    users = c.fetchall()
    conn.close()
    return jsonify([{'username': u[0], 'level': u[1], 'score': u[2]} for u in users])

# --- ระบบรับสัญญาณจาก GitHub (Webhook) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    subprocess.run(['git', 'pull', 'origin', 'main'], cwd='/home/panusddn/mysite')
    subprocess.run(['touch', '/var/www/panusddn_pythonanywhere_com_wsgi.py'])
    return "Updated successfully", 200   
init_db()

if __name__ == '__main__':
    
    app.run(debug=True, port=5000)
