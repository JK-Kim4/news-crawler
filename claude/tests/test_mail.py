import pytest
from auth.mail import MailSender, SmtpMailSender


def test_mail_sender_is_abstract():
    with pytest.raises(TypeError):
        MailSender()


def test_smtp_mail_sender_init():
    sender = SmtpMailSender(
        host="smtp.test.com",
        port=587,
        user="u",
        password="p",
        sender_email="from@test.com",
    )
    assert sender.host == "smtp.test.com"


def test_smtp_mail_sender_send(monkeypatch):
    sent = []

    class FakeSmtp:
        def __init__(self, host, port):
            self.host = host
            self.port = port
        def starttls(self): pass
        def login(self, user, password): pass
        def sendmail(self, from_addr, to_addr, msg):
            sent.append({"from": from_addr, "to": to_addr, "msg": msg})
        def quit(self): pass

    import auth.mail as mail_mod
    monkeypatch.setattr(mail_mod.smtplib, "SMTP", FakeSmtp)

    sender = SmtpMailSender(
        host="smtp.test.com", port=587,
        user="u", password="p", sender_email="from@test.com",
    )
    sender.send("to@test.com", "Subject", "Body")
    assert len(sent) == 1
    assert sent[0]["to"] == "to@test.com"
