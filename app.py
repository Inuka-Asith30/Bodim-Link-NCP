from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "bodim_link_secret_key"

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'bodim_link_ncp'

def get_db_connection():
    try:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"Database Connection Warning: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

# ----------------------------------------------------
# Task A: User Registration (Theneth)
# ----------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        
        hashed_password = generate_password_hash(password)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO users (name, phone, email, password, role) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (name, phone, email, hashed_password, role))
                
                # If owner uploads bill (optional as per original logic)
                if role == 'owner' and 'electricity_bill' in request.files:
                    bill_file = request.files['electricity_bill']
                    if bill_file.filename != '':
                        filename = secure_filename(bill_file.filename)
                        bill_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        bill_file.save(bill_path)
                        
            connection.commit() 
            flash('Registration Successful! Please login.', 'success')
            return redirect(url_for('login')) 
            
        except pymysql.MySQLError as e:
            connection.rollback() 
            flash('Email already used!', 'danger')
            print(f"Database error: {e}")
            
        finally:
            connection.close()

    return render_template('register.html')


# ----------------------------------------------------
# Task B: User Login (Theneth)
# ----------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                if user and check_password_hash(user['password'], password):
                    session['user_id'] = user['id']
                    session['user_name'] = user['name']
                    session['user_role'] = user['role']
                    
                    if user['role'] == 'student':
                        return redirect(url_for('student_dashboard'))
                    elif user['role'] == 'owner':
                        return redirect(url_for('owner_dashboard'))
                    elif user['role'] == 'admin':
                        return redirect(url_for('admin_dashboard'))
                else:
                    flash('Incorrect Password or Email', 'danger')
                    
        except pymysql.MySQLError as e:
            flash('Database Error!', 'danger')
            print(f"Database error: {e}")
            
        finally:
            connection.close()

    return render_template('login.html')


# ----------------------------------------------------
# Dashboards and Logout
# ----------------------------------------------------
@app.route('/student')
def student_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    return render_template('student_dashboard.html')

@app.route('/owner')
def owner_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('login'))
    return render_template('owner_dashboard.html')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/my_listings')
def my_listings():
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('login'))
        
    connection = get_db_connection()
    boardings = []
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM boardings WHERE owner_id = %s", (session['user_id'],))
                boardings = cursor.fetchall()
        except Exception as e:
            print(f"Database Error: {e}")
        finally:
            connection.close()
            
    return render_template('my_listings.html', boardings=boardings)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/boarding/<int:id>')
def boarding_details(id):
    return render_template('boarding_details.html')


# ----------------------------------------------------
# Sahan's Add Boarding Logic (Preserved)
# ----------------------------------------------------
@app.route('/add_boarding', methods=['POST'])
def add_boarding():
    owner_id = session.get('user_id', 1) 
    location = request.form.get('location')
    rent = request.form.get('rent')
    amenities = request.form.get('amenities')
    gender_preference = request.form.get('gender_preference')
    
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"uploads/{filename}"
            
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO boardings (owner_id, location, rent, amenities, gender_preference, image_path)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (owner_id, location, rent, amenities, gender_preference, image_path))
            connection.commit()
        except Exception as e:
            connection.rollback()
            print(f"Error: {e}")
        finally:
            connection.close()
        
    return redirect(url_for('owner_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
