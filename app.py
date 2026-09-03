from flask import Flask, render_template

app = Flask(__name__)

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

@app.route('/boarding/<int:id>')
def boarding_details(id):
    return render_template('boarding_details.html')

if __name__ == '__main__':
    app.run(debug=True)
