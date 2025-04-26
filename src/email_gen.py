import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(sender_email, sender_password, recipient_email, subject, body):
    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Create a secure SSL context and connect to the SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(sender_email, sender_password)  # Log in to your email account
            server.send_message(msg)  # Send the email
            print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")

# Example usage
sender_email = 'your_email@gmail.com'
sender_password = 'your_password'  # Use App Password if using Gmail with 2FA
recipient_email = 'recipient@example.com'
subject = 'Hello from Python'
body = 'This is a test email sent from Python!'

send_email(sender_email, sender_password, recipient_email, subject, body)
