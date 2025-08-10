from email.mime.text import MIMEText
import smtplib
from typing import Iterable

class GmailSender:
    """Send emails from a Gmail account that gets authenticated using an app password"""

    def __init__(self, sender_address: str, sender_app_password: str, recipient_address: str | Iterable[str]):
        self.sender_address = sender_address
        self.sender_app_password = sender_app_password
        self.recipient_address = recipient_address
    
    def plain_text(self, subject: str, body: str):
        """Send a plain text email body"""

        recipient_address = tuple(self.recipient_address,) if isinstance(self.recipient_address, str) else self.recipient_address

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.sender_address
        msg["To"] = ", ".join(recipient_address)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
            smtp_server.login(self.sender_address, self.sender_app_password)
            smtp_server.sendmail(self.sender_address, recipient_address, msg.as_string())
