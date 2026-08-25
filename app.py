from flask import Flask, render_template

# Initialize the Flask application
app = Flask(__name__)

# Define the main route (Home Page)
@app.route('/')
def home():
    # This will send the index.html file to the user's browser
    return render_template('index.html')

if __name__ == '__main__':
    # Run the application in debug mode
    app.run(debug=True, port=5000)