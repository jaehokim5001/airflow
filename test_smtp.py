#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
import sys

try:
    msg = MIMEText('Airflow SMTP Test Body')
    msg['Subject'] = 'Airflow SMTP Test Subject'
    msg['From'] = 'j.h.kim6844@gmail.com'
    msg['To'] = 'jhk5055@nate.com'

    # Port 587 for STARTTLS
    print("Connecting to smtp.gmail.com:587 with STARTTLS...")
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('j.h.kim6844@gmail.com', 'twsexivomyswgeca')
        server.send_message(msg)
        print("Test Email sent successfully to jhk5055@nate.com")
except Exception as e:
    print(f"Failed to send email: {e}")
    sys.exit(1)
