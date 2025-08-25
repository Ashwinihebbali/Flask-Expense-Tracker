from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',          # Your MySQL password
    'database': 'expense_tracker'
}

# Initialize DB tables
def init_db():
    conn = mysql.connector.connect(**db_config)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            category VARCHAR(50) NOT NULL,
            date DATE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------------- Signup ----------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = mysql.connector.connect(**db_config)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            return redirect(url_for('login'))
        except mysql.connector.errors.IntegrityError:
            return render_template('signup.html', error="Username already exists!")
        finally:
            conn.close()
    return render_template('signup.html')

# ---------------------- Login ----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = mysql.connector.connect(**db_config)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password!")
    return render_template('login.html')

# ---------------------- Logout ----------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------------- Dashboard ----------------------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = mysql.connector.connect(**db_config)
    c = conn.cursor()
    c.execute("SELECT * FROM expenses WHERE user_id=%s ORDER BY date DESC", (session['user_id'],))
    expenses = c.fetchall()
    c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=%s", (session['user_id'],))
    total_expense = c.fetchone()[0] or 0
    conn.close()
    return render_template('index.html', expenses=expenses, total_expense=total_expense)

# ---------------------- Add Expense ----------------------
@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']
        conn = mysql.connector.connect(**db_config)
        c = conn.cursor()
        c.execute("INSERT INTO expenses (user_id, amount, category, date) VALUES (%s, %s, %s, %s)",
                  (session['user_id'], amount, category, date))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_expense.html')

# ---------------------- Delete Expense ----------------------
@app.route('/delete/<int:id>')
def delete_expense(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = mysql.connector.connect(**db_config)
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=%s AND user_id=%s", (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
