from flask import Flask, render_template, request, session, redirect, url_for, flash
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
DB_NAME = 'database'

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/student')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/owner')
def owner_dashboard():
    return render_template('owner_dashboard.html')

@app.route('/admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/boardings')
def boardings():
    return render_template('boardings.html')

@app.route('/boarding/<int:id>')
def boarding_details(id):
    return render_template('boarding_details.html')

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
