"""
自定义邮件后端：通过 Resend REST API 发送邮件
PythonAnywhere 免费版封了 SMTP 端口，但允许 HTTPS，所以用 API 方式。
"""
import resend
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class ResendBackend(BaseEmailBackend):
    """使用 Resend REST API 发送邮件"""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        resend.api_key = settings.RESEND_API_KEY

    def send_messages(self, email_messages):
        count = 0
        for message in email_messages:
            try:
                params = {
                    "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
                    "to": message.to,
                    "subject": message.subject,
                    "text": message.body,
                }
                if message.alternatives:
                    for alt_content, alt_type in message.alternatives:
                        if alt_type == "text/html":
                            params["html"] = alt_content
                            break

                resend.Emails.send(params)
                count += 1
            except Exception as e:
                if not self.fail_silently:
                    raise
                print(f"Resend 发送失败: {e}")
        return count
