"""邮件发送模块（QQ邮箱SMTP）"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


def send_email(config, subject, body):
    """
    发送邮件
    config: {
        "smtp_server": "smtp.qq.com",
        "smtp_port": 465,
        "sender": "your_email@qq.com",
        "password": "authorization_code",  # QQ邮箱授权码
        "receiver": "1737730809@qq.com"
    }
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = config["sender"]
    msg["To"] = config["receiver"]

    # HTML正文
    html_part = MIMEText(body, "html", "utf-8")
    msg.attach(html_part)

    try:
        if config.get("smtp_port") == 465:
            server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], timeout=30)
        else:
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=30)
            server.starttls()

        server.login(config["sender"], config["password"])
        server.sendmail(config["sender"], config["receiver"], msg.as_string())
        server.quit()
        return True, "邮件发送成功"
    except smtplib.SMTPAuthenticationError:
        return False, "邮箱授权码错误，请检查"
    except smtplib.SMTPException as e:
        return False, f"邮件发送失败: {e}"
    except Exception as e:
        return False, f"发送异常: {e}"
