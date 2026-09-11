import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template
import os  # <-- Add this line right here!

def send_welcome_email(user_email, user_name):
    # --- Configuration ---
    # We will use Gmail for testing. You will need to put your email here later.
    SENDER_EMAIL = "your_email@gmail.com"  
    SENDER_PASSWORD = "your_app_password"  

    SENDER_EMAIL = os.environ.get("MAIL_USERNAME")  
    SENDER_PASSWORD = os.environ.get("MAIL_PASSWORD")  
    
    try:
        # 1. Render your HTML template into an email format
        # This will use the welcome_student.html file you designed
        html_content = render_template('emails/welcome_student.html', name=user_name)
        
        # 2. Setup the Email structure
        msg = MIMEMultipart("alternative")
        msg['Subject'] = "Welcome to Bodim-Link NCP!"
        msg['From'] = f"Bodim-Link <{SENDER_EMAIL}>"
        msg['To'] = user_email
        
        # Attach the HTML you designed
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        # 3. Send the Email using Gmail's server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Success: Welcome email sent to {user_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
