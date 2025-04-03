import random
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

def generate_otp():
    return str(random.randint(100000, 999999))

def send_email(receiver_email: str, otp: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    subject = "Your OTP Code"
    body = f"Your OTP is {otp}. It will expire in 10 minutes."
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    
    print(f"Sending email to {receiver_email} with OTP {otp}")
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("Starting TLS...")
            server.starttls()
            print("Logging in...")
            server.login(sender_email, sender_password)
            print("Sending email...")
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise Exception(f"Error sending email: {str(e)}")