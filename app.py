from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import os
from werkzeug.utils import secure_filename
import random
import smtplib
from email.mime.text import MIMEText

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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed. Please try again later.', 'danger')
            return render_template('register.html')

        try:
            with connection.cursor() as cursor:
                #  Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('Email already used!', 'danger')
                    return render_template('register.html')
                
                #  Save file if owner
                bill_filename = None
                if role == 'owner' and 'electricity_bill' in request.files:
                    bill_file = request.files['electricity_bill']
                    if bill_file.filename != '':
                        filename = secure_filename(bill_file.filename)
                        bill_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        bill_file.save(bill_path)
                        bill_filename = filename
                
                #  Generate OTP
                otp = str(random.randint(100000, 999999))
                
                #  Save details temporarily in session
                session['reg_data'] = {
                    'name': name,
                    'phone': phone,
                    'email': email,
                    'password': password,  # We will hash it later after verification
                    'role': role,
                    'bill_filename': bill_filename
                }
                session['reg_otp'] = otp
                
                #  Send OTP Email
                try:
                    msg = MIMEText(f"Welcome to Bodim-Link NCP! Your registration verification OTP is: {otp}")
                    msg['Subject'] = 'Account Verification OTP'
                    msg['From'] = MAIL_USERNAME
                    msg['To'] = email
                    
                    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    server.login(MAIL_USERNAME, MAIL_PASSWORD)
                    server.send_message(msg)
                    server.quit()
                    
                    flash('An OTP has been sent to your email to verify your account.', 'success')
                except Exception as e:
                    print(f"Email sending failed: {e}")
                    flash(f'TESTING MODE: Your Registration OTP is {otp}', 'info')
                
                return redirect(url_for('verify_register_otp'))
                
        finally:
            connection.close()

    return render_template('register.html')

@app.route('/verify_register_otp', methods=['GET', 'POST'])
def verify_register_otp():
    if 'reg_data' not in session or 'reg_otp' not in session:
        flash('Session expired. Please register again.', 'danger')
        return redirect(url_for('register'))
        
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        
        if user_otp == session['reg_otp']:
            # Verification successful! Save to database.
            data = session['reg_data']
            hashed_password = generate_password_hash(data['password'])
            
            connection = get_db_connection()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        sql = "INSERT INTO users (name, phone, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)"
                        cursor.execute(sql, (data['name'], data['phone'], data['email'], hashed_password, data['role']))
                        user_id = cursor.lastrowid
                        
                        # Save bill verification if owner
                        if data['role'] == 'owner' and data.get('bill_filename'):
                            bill_sql = "INSERT INTO owner_verifications (owner_id, bill_image_path) VALUES (%s, %s)"
                            cursor.execute(bill_sql, (user_id, f"uploads/{data['bill_filename']}"))
                            
                    connection.commit()
                    
                    # Clear session
                    session.pop('reg_data', None)
                    session.pop('reg_otp', None)
                    
                    flash('Registration Successful! Your account has been verified. Please login.', 'success')
                    return redirect(url_for('login'))
                except Exception as e:
                    connection.rollback()
                    print(f"Database error during registration: {e}")
                    flash('Error creating account. Please try again.', 'danger')
                finally:
                    connection.close()
        else:
            flash('Invalid OTP! Please try again.', 'danger')
            
    return render_template('verify_register_otp.html')


# ----------------------------------------------------
# Task B: User Login (Theneth)
# ----------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        connection = get_db_connection()
        if not connection:
            flash('Database connection failed. Please try again later.', 'danger')
            return render_template('login.html')

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                if user and check_password_hash(user['password_hash'], password):
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
                    flash('Invalid email or password!', 'danger')
                    
        except pymysql.MySQLError as e:
            flash('An error occurred during login.', 'danger')
            print(f"Database error: {e}")
            
        finally:
            if connection:
                connection.close()

    return render_template('login.html')


# ----------------------------------------------------
# Dashboards and Logout
# ----------------------------------------------------
@app.route('/student')
def student_dashboard():
    
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
        

    connection = get_db_connection()
    boardings = [] 
    
    if connection:
        try:
            with connection.cursor() as cursor:
                
                cursor.execute("SELECT * FROM boardings WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) ORDER BY id DESC")
            
                boardings = cursor.fetchall()
        except Exception as e:
            print(f"Database Error: {e}")
        finally:
            connection.close()
            
    
    return render_template('student_dashboard.html', boardings=boardings)
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

@app.route('/owner_bookings')
def owner_bookings():
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('login'))
        
    owner_id = session['user_id']
    connection = get_db_connection()
    bookings = []
    
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                    SELECT vr.*, u.name as student_name, u.phone as student_phone, b.location as boarding_location
                    FROM visit_requests vr
                    JOIN users u ON vr.student_id = u.id
                    JOIN boardings b ON vr.boarding_id = b.id
                    WHERE vr.owner_id = %s
                    ORDER BY vr.created_at DESC
                """
                cursor.execute(sql, (owner_id,))
                bookings = cursor.fetchall()
        except Exception as e:
            print(f"Database error: {e}")
        finally:
            connection.close()
            
    return render_template('owner_bookings.html', bookings=bookings)

@app.route('/accept_visit/<int:id>')
def accept_visit(id):
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('login'))
        
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE visit_requests SET status = 'accepted' WHERE id = %s AND owner_id = %s", (id, session['user_id']))
            connection.commit()
            flash('Visit request accepted!', 'success')
        except Exception as e:
            connection.rollback()
            print(f"Database error: {e}")
            flash('Error accepting request.', 'danger')
        finally:
            connection.close()
            
    return redirect(url_for('owner_bookings'))


@app.route('/reject_visit/<int:id>')
def reject_visit(id):
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('login'))
        
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE visit_requests SET status = 'rejected' WHERE id = %s AND owner_id = %s", (id, session['user_id']))
            connection.commit()
            flash('Visit request rejected.', 'info')
        except Exception as e:
            connection.rollback()
            print(f"Database error: {e}")
            flash('Error rejecting request.', 'danger')
        finally:
            connection.close()
            
    return redirect(url_for('owner_bookings'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/boarding/<int:id>')
def boarding_details(id):
    connection = get_db_connection()
    boarding = None
    
    if connection:
        try:
            with connection.cursor() as cursor:
                #  Retrive bodinm info using its ID
                cursor.execute("SELECT * FROM boardings WHERE id = %s", (id,))
                boarding = cursor.fetchone() # using fetchone() because 1-bodim
                
        except Exception as e:
            print(f"Database Error: {e}")
        finally:
            connection.close()
            
  
    if not boarding:
        flash('Cannot Find!', 'danger')
        return redirect(url_for('student_dashboard'))
        
    # Send bodim data to front end
    return render_template('boarding_details.html', boarding=boarding)

@app.route('/student-requests')
def student_requests():
    return render_template('student_requests.html')


# ----------------------------------------------------
# Sahan's Add Boarding Logic (Preserved)
# ----------------------------------------------------
@app.route('/add_boarding', methods=['POST'])
def add_boarding():
    owner_id = session.get('user_id', 1) 
    
    # Get all fields from HTML form
    name = request.form.get('boarding_name', 'Unnamed Boarding')
    location = request.form.get('location', '')
    address = request.form.get('address', '')
    monthly_rent = request.form.get('rent', 0)
    security_deposit = request.form.get('deposit', 0)
    gender_preference = request.form.get('gender_preference', 'any')
    # boys -> male, girls -> female
    if gender_preference == 'boys':
        gender_preference = 'male'
    elif gender_preference == 'girls':
        gender_preference = 'female'
        
    boarding_type = request.form.get('type', 'Full Boarding')
    description = request.form.get('description', '')
    amenities = request.form.get('amenities', '')
    
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
                # Add image_path column if it doesn't exist (safety check)
                try:
                    cursor.execute("ALTER TABLE boardings ADD COLUMN image_path VARCHAR(255)")
                except:
                    pass # Column already exists
                    
                sql = """
                    INSERT INTO boardings (owner_id, name, location, address, monthly_rent, security_deposit, gender_preference, boarding_type, description, image_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (owner_id, name, location, address, monthly_rent, security_deposit, gender_preference, boarding_type, description, image_path))
                boarding_id = cursor.lastrowid
                
                # Insert facilities if amenities provided
                if amenities:
                    wifi = 1 if 'wifi' in amenities.lower() else 0
                    meals = 1 if 'meal' in amenities.lower() else 0
                    study = 1 if 'study' in amenities.lower() else 0
                    cursor.execute("INSERT INTO facilities (boarding_id, wifi, meals, study_room) VALUES (%s, %s, %s, %s)", 
                                  (boarding_id, wifi, meals, study))
                                  
            connection.commit()
            flash('Boarding added successfully!', 'success')
        except Exception as e:
            connection.rollback()
            print(f"Error adding boarding: {e}")
            flash('Error adding boarding. Please check your details.', 'danger')
        finally:
            connection.close()
        
    return redirect(url_for('owner_dashboard'))


# ----------------------------------------------------
# New Features (Search & Visit Requests)
# ----------------------------------------------------
@app.route('/search', methods=['GET'])
def search_boardings():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
        
    location = request.args.get('location')
    max_price = request.args.get('max_price')
    gender = request.args.get('gender')

    query = "SELECT * FROM boardings WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
    params = []

    if location:
        query += " AND location LIKE %s"
        params.append(f"%{location}%")
    if max_price and max_price.strip():
        query += " AND rent <= %s"
        params.append(float(max_price))
    if gender and gender != 'any':
        query += " AND gender_preference = %s"
        params.append(gender)

    query += " ORDER BY id DESC"

    connection = get_db_connection()
    boardings = []
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(params))
                boardings = cursor.fetchall()
        except Exception as e:
            print(f"Database error: {e}")
        finally:
            connection.close()

    return render_template('student_dashboard.html', boardings=boardings)

@app.route('/request_visit', methods=['POST'])
def request_visit():
    if 'user_id' not in session or session.get('user_role') != 'student':
        flash('Please login as a student to book a visit.', 'danger')
        return redirect(url_for('login'))
    
    boarding_id = request.form.get('boarding_id')
    owner_id = request.form.get('owner_id')
    visit_dates = request.form.get('visit_dates')
    student_id = session['user_id']
    
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS visit_requests (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        student_id INT NOT NULL,
                        boarding_id INT NOT NULL,
                        owner_id INT NOT NULL,
                        visit_dates VARCHAR(255) NOT NULL,
                        status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                sql = "INSERT INTO visit_requests (student_id, boarding_id, owner_id, visit_dates) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (student_id, boarding_id, owner_id, visit_dates))
            connection.commit()
            flash('Visit request sent to the owner successfully!', 'success')
        except Exception as e:
            print(f"Database error: {e}")
            flash('Error sending visit request.', 'danger')
        finally:
            connection.close()
            
    return redirect(url_for('boarding_details', id=boarding_id))

# ----------------------------------------------------
# Forgot Password & OTP Logic (Theneth)
# ----------------------------------------------------
MAIL_USERNAME = "email_email@gmail.com"
MAIL_PASSWORD = "app_password"

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        connection = get_db_connection()
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                    user = cursor.fetchone()
                    
                    if user:
                        otp = str(random.randint(100000, 999999))
                        session['reset_otp'] = otp
                        session['reset_email'] = email
                        
                        try:
                            msg = MIMEText(f"Your Bodim-Link NCP password reset OTP is: {otp}")
                            msg['Subject'] = 'Password Reset OTP'
                            msg['From'] = MAIL_USERNAME
                            msg['To'] = email
                            
                            # Using Gmail SMTP - For testing, this might fail without real credentials,
                            # but the logic is fully implemented.
                            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                            server.login(MAIL_USERNAME, MAIL_PASSWORD)
                            server.send_message(msg)
                            server.quit()
                            
                            flash('OTP has been sent to your email.', 'success')
                            return redirect(url_for('verify_otp'))
                        except Exception as e:
                            print(f"Email sending failed: {e}")
                            # FLASH OTP FOR LOCAL TESTING SINCE NO REAL EMAIL CONFIGURED
                            flash(f'TESTING MODE: Your OTP is {otp}', 'info')
                            return redirect(url_for('verify_otp'))
                    else:
                        flash('Email not found in our system.', 'danger')
            finally:
                connection.close()
                
    return render_template('forgot_password.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        
        if 'reset_otp' in session and session['reset_otp'] == user_otp:
            flash('OTP Verified! Please enter your new password.', 'success')
            return redirect(url_for('reset_password'))
        else:
            flash('Invalid OTP! Please try again.', 'danger')
            
    return render_template('verify_otp.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session or 'reset_otp' not in session:
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        new_password = request.form.get('password')
        hashed_password = generate_password_hash(new_password)
        email = session['reset_email']
        
        connection = get_db_connection()
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hashed_password, email))
                connection.commit()
                
                session.pop('reset_otp', None)
                session.pop('reset_email', None)
                
                flash('Password reset successful! You can now login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                connection.rollback()
                print(f"Database error: {e}")
                flash('Failed to reset password.', 'danger')
            finally:
                connection.close()
                
    return render_template('reset_password.html')



# ----------------------------------------------------
# Static Pages & Profile Routes
# ----------------------------------------------------
@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    new_name = request.form.get('name')
    user_id = session['user_id']
    
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE users SET name = %s WHERE id = %s", (new_name, user_id))
            connection.commit()
            session['user_name'] = new_name
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            connection.rollback()
            print(f"Error updating profile: {e}")
            flash('Error updating profile.', 'danger')
        finally:
            connection.close()
            
    return redirect(url_for('profile'))


@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('messages.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')


@app.route('/delete_boarding/<int:id>', methods=['POST'])
def delete_boarding(id):
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('login'))
        
    owner_id = session['user_id']
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Verify ownership before deleting
                cursor.execute("SELECT * FROM boardings WHERE id = %s AND owner_id = %s", (id, owner_id))
                if cursor.fetchone():
                    # Delete facilities first (foreign key constraints)
                    cursor.execute("DELETE FROM facilities WHERE boarding_id = %s", (id,))
                    # Delete reviews
                    cursor.execute("DELETE FROM reviews WHERE boarding_id = %s", (id,))
                    # Finally delete boarding
                    cursor.execute("DELETE FROM boardings WHERE id = %s", (id,))
                    connection.commit()
                    flash('Boarding deleted successfully.', 'success')
                else:
                    flash('Unauthorized to delete this boarding.', 'danger')
        except Exception as e:
            print(f"Error deleting: {e}")
            connection.rollback()
            flash('Error occurred while deleting.', 'danger')
        finally:
            connection.close()
            
    return redirect(url_for('my_listings'))

if __name__ == '__main__':
    app.run(debug=True)
