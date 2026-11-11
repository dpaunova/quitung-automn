from __future__ import annotations

import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_report_email(
    to_email: str,
    accountant_name: str,
    business_name: str,
    month: str,
    excel_path: str,
    pdf_path: str | None = None,
    receipt_count: int = 0,
    total_sum: float = 0.0,
) -> bool:
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured — skipping email send to %s", to_email)
        return False

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = f"Месечен отчет за {business_name} — {month}"

    body = (
        f"Уважаеми/а {accountant_name},\n\n"
        f"Приложен е месечният отчет на {business_name} за {month}.\n\n"
        f"Общо бележки: {receipt_count}\n"
        f"Обща сума: {total_sum:.2f} лв.\n\n"
        f"Моля, проверете маркираните в жълто полета — те са с ниска "
        f"сигурност при автоматичното разпознаване.\n\n"
        f"С уважение,\nBeleg Scanner"
    )
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for fpath in [excel_path, pdf_path]:
        if fpath and Path(fpath).exists():
            with open(fpath, "rb") as f:
                part = MIMEApplication(f.read())
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=Path(fpath).name,
                )
                msg.attach(part)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("Report email sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Failed to send report email to %s", to_email)
        return False
