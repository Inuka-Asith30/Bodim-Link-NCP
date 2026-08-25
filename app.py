from flask import Flask, render_template
import pymysql

# Initialize the Flask application
app = Flask(__name__)

# Database Connection Details (Using XAMPP default settings)
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "bodim_link_ncp"

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# Define the main route (Home Page)
@app.route('/')
def home():
    # Test Database Connection
    try:
        conn = get_db_connection()
        conn.close()
        db_status = "Database Connected Successfully! ✅"
    except Exception as e:
        db_status = f"Database Connection Failed! ❌ Error: {e}"

    # This will send the index.html file to the user's browser
    return render_template('index.html', db_status=db_status)

if __name__ == '__main__':
    # Run the application in debug mode
    app.run(debug=True, port=5000)