"""Outbound email for self-service password recovery.

Development and tests point SMTP at the `mailpit` compose service
(127.0.0.1:1026); production configures a real relay. Delivery failures
never surface to the caller of the reset-request endpoint (the response
must not reveal whether an address exists), so they are logged without
the recipient or the one-time code.
"""

import logging
import smtplib
from email.message import EmailMessage

from ..config import Settings

logger = logging.getLogger(__name__)


class Mailer:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.smtp_host.strip() and self.settings.smtp_from.strip())

    def send_password_reset_otp(
        self, to_email: str, otp: str, expires_minutes: int
    ) -> bool:
        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = to_email
        message["Subject"] = "DBCAS verification code / Mã xác minh DBCAS"
        message.set_content(
            "Hello,\n\n"
            "Someone requested a password reset for your DBCAS account. "
            f"Your verification code is:\n\n    {otp}\n\n"
            f"It expires in {expires_minutes} minutes. Never share this code with anyone.\n\n"
            "If you did not request this, ignore this email — your password will not change.\n\n"
            "—\n"
            "Xin chào,\n\n"
            "Đã có yêu cầu đặt lại mật khẩu cho tài khoản DBCAS của bạn. "
            f"Mã xác minh của bạn là:\n\n    {otp}\n\n"
            f"Mã có hiệu lực trong {expires_minutes} phút. Tuyệt đối không chia sẻ mã này cho bất kỳ ai.\n\n"
            "Nếu bạn không thực hiện yêu cầu này, hãy bỏ qua email — mật khẩu sẽ không thay đổi.\n"
        )
        try:
            self._deliver(message)
        except (smtplib.SMTPException, OSError, ValueError) as exc:
            # Never log the address or the code; the exception type is
            # enough to diagnose a broken relay.
            logger.warning(
                "Password reset email delivery failed: %s", exc.__class__.__name__
            )
            return False
        return True

    def _deliver(self, message: EmailMessage) -> None:
        s = self.settings
        if s.smtp_ssl:
            client = smtplib.SMTP_SSL(
                s.smtp_host, s.smtp_port, timeout=s.smtp_timeout_seconds
            )
        else:
            client = smtplib.SMTP(
                s.smtp_host, s.smtp_port, timeout=s.smtp_timeout_seconds
            )
        with client:
            if s.smtp_starttls and not s.smtp_ssl:
                client.starttls()
            if s.smtp_username:
                client.login(s.smtp_username, s.smtp_password)
            client.send_message(message)
