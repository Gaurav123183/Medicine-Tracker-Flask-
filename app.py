from flask import Flask, request, redirect, url_for, session, render_template
from flask_mysqldb import MySQL
import MySQLdb.cursors
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ✅ Database Config
app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")
app.config['MYSQL_PORT'] = int(os.getenv("MYSQL_PORT"))
mysql = MySQL(app)

# ✅ Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email=%s', (email,))
        acc = cursor.fetchone()

        if acc:
            msg = "Account already exists!"
        else:
            cursor.execute(
                'INSERT INTO users (name, email, password) VALUES (%s, %s, %s)',
                (name, email, password)
            )
            mysql.connection.commit()
            return redirect(url_for('login'))

    return render_template("register.html", msg=msg)

# ✅ Login
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email=%s AND password=%s', (email, password))
        user = cursor.fetchone()

        if user:
            session['loggedin'] = True
            session['id'] = user['user_id']
            session['name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            msg = "Incorrect email or password"

    return render_template("login.html", msg=msg)

# ✅ Dashboard
@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM medicines WHERE user_id=%s', (session['id'],))
    meds = cursor.fetchall()

    return render_template("dashboard.html", meds=meds, name=session['name'])

# ✅ Add Medicine
@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        data = (
            session['id'],
            request.form['med_name'],
            request.form['dosage'],
            request.form['frequency'],
            request.form['start_date'],
            request.form['end_date'],
            request.form['notes']
        )
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('''INSERT INTO medicines (user_id, med_name, dosage, frequency, start_date, end_date, notes)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)''', data)
        mysql.connection.commit()
        return redirect(url_for('dashboard'))

    return render_template("add.html")

# ✅ Update Medicine
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM medicines WHERE med_id=%s AND user_id=%s', (id, session['id']))
    med = cur.fetchone()

    if request.method == "POST":
        cur.execute('''UPDATE medicines SET med_name=%s, dosage=%s, frequency=%s, start_date=%s, end_date=%s, notes=%s 
                       WHERE med_id=%s''', (
            request.form['med_name'], request.form['dosage'], request.form['frequency'],
            request.form['start_date'], request.form['end_date'], request.form['notes'], id))
        mysql.connection.commit()
        return redirect(url_for('dashboard'))

    return render_template("update.html", med=med)

# ✅ Delete
@app.route('/delete/<int:id>')
def delete(id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('DELETE FROM medicines WHERE med_id=%s AND user_id=%s', (id, session['id']))
    mysql.connection.commit()
    return redirect(url_for('dashboard'))

# ✅ Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
