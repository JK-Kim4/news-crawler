import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText


class MailSender(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpMailSender(MailSender):
    def __init__(self, host: str, port: int, user: str, password: str, sender_email: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.sender_email = sender_email

    def send(self, to: str, subject: str, body: str) -> None:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = to
        server = smtplib.SMTP(self.host, self.port)
        try:
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.sender_email, to, msg.as_string())
        finally:
            server.quit()
