# app/utils/mailer.py
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from app.core.config import settings

def send_email_sync(to_email: str, subject: str, html_body: str):
    """
    Simple, robust SMTP sender. If SMTP is not configured, it silently no-ops
    (dev-friendly) but you’ll see a print log.
    """
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        print("[mailer] SMTP is not configured. Skipping email send.")
        return

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((settings.SMTP_FROM_NAME or "Toys Catalog", settings.SMTP_FROM))
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
    except Exception as e:
        # dev-friendly: xatoni yutib yuborish (BackgroundTasks ichida)
        print(f"[mailer] Failed to send email to {to_email}: {e}")

def build_welcome_email(customer_name: str, email: str, password: str) -> tuple[str, str]:
    subject = "Welcome to Toys Catalog — Your Account Password"
    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:auto;">
      <h2 style="color:#222;">Salom, {customer_name}!</h2>
      <p>Siz Toys Catalog’da muvaffaqiyatli ro‘yxatdan o‘tdingiz.</p>
      <p><b>Kirish ma’lumotlari:</b></p>
      <ul>
        <li>Email: <b>{email}</b></li>
        <li>Parol: <b>{password}</b></li>
      </ul>
      <p>Xavfsizlik uchun ushbu parolni iloji boricha tezroq o‘zgartirishingizni tavsiya qilamiz.</p>
      <hr>
      <p style="color:#888;font-size:12px;">Agar bu amal siz tomonidan bajarilmagan bo‘lsa, darhol javob yozing.</p>
    </div>
    """
    return subject, html