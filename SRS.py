from flask import Flask, request, render_template, send_file, redirect, url_for, session, flash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import sqlite3
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
def init_db():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY, name TEXT, phone INTEGER, class TEXT, email TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'email' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('register_student'))

@app.route('/register_student')
def register_student():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    name = request.form['name']
    phone = request.form['phone']
    student_class = request.form['class']
    email = request.form['email']

    if not email.endswith('@mubas.ac.mw'):
        return "Error: Email must end with '@mubas.ac.mw'."

    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM students WHERE email = ?", (email,))
    if c.fetchone()[0] > 0:
        conn.close()
        return "Error: This email is already registered."

    c.execute("INSERT INTO students (name, phone, class, email) VALUES (?, ?, ?, ?)", 
              (name, phone, student_class, email))
    conn.commit()
    conn.close()
    
    return "Student Registered Successfully!"

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
        if c.fetchone()[0] > 0:
            conn.close()
            return "Error: This email is already registered."
        
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        conn.close()
        
        return "User Registered Successfully!"
    
    return render_template('register_user.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        
        c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['email'] = email
            return redirect(url_for('register_student'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/generate_pdf')
def generate_pdf():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    class_mapping = {
        'Electrical Technology': 'ELT',
        'Motor Vehicle Technology': 'MVT',
        'Wood Technology': 'WDT',
        'Welding Technology': 'WET'
    }

    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT name, phone, class, email FROM students")
    students = c.fetchall()
    conn.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 40
    p.drawString(30, y, "Student Details")
    y -= 20
    p.drawString(30, y, "Name")
    p.drawString(15, y, "Phone")
    p.drawString(230, y, "Class")
    p.drawString(330, y, "Email")
    y -= 20

    for student in students:
        p.drawString(30, y, student[0])
        p.drawString(130, y, str(student[1]))
        abbreviated_class = class_mapping.get(student[2], student[2])
        p.drawString(230, y, abbreviated_class)
        p.drawString(330, y, student[3])
        y -= 20

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='Registered_students.pdf', mimetype='application/pdf')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
