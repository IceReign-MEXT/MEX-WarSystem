import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load from config
with open("config.json", "r") as file:
    config = json.load(file)

TELEGRAM_TOKEN = config["telegram_token"]
CHAT_ID = config["telegram_chat_id"]
EMAILS = config["emails"]
EMAIL_SENDER = config["email_sender"]
EMAIL_PASSWORD = config["email_password"]

def send_email(subject, message):
    for email in EMAILS:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, email, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Error sending email to {email}: {e}")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def alert_all(subject, message):
    send_email(subject, message)
    send_telegram(f"{subject}\n{message}")

if __name__ == "__main__":
    alert_all("🚨 MEX ALERT", "⚠️ Potential wallet compromise detected. Sweeping now...")