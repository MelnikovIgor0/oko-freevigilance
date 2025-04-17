from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from os.path import basename
import smtplib
from typing import Union, List

def send_email(
    mail_from: str,
    token: str,
    mail_to: List[str],
    text: str,
    subject: str = None
) -> None:
    msg = MIMEMultipart()
    msg['From'] = mail_from
    msg['To'] = COMMASPACE.join(mail_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject if subject else ''
    msg.attach(MIMEText(text))
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpObj.starttls()
    smtpObj.login(mail_from, token)
    smtpObj.sendmail(mail_from, mail_to, msg.as_string())
    smtpObj.quit()
