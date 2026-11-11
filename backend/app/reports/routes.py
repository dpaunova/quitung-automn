import datetime
import os
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Business, MonthlyReport, Receipt, User
from app.reports.excel_generator import generate_excel

router = APIRouter(prefix="/api/reports", tags=["reports"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PreviewOut(BaseModel):
    month: str
    receipt_count: int
    total_sum: float
    vat_sum: float
    netto_sum: float


class SendRequest(BaseModel):
    month: str  # YYYY-MM


class ReportOut(BaseModel):
    id: int
    month: str
    sent_at: datetime.datetime | None = None
    sent_to_email: str | None = None
    receipt_count: int
    total_sum: float
    excel_path: str | None = None
    pdf_path: str | None = None

    model_config = {"from_attributes": True}


class SendResponse(BaseModel):
    message: str
    report_id: int
    excel_path: str
    pdf_path: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_receipts_for_month(db: Session, business_id: int, month: str) -> list[Receipt]:
    """Fetch done receipts for a business in a given YYYY-MM month."""
    year, mon = month.split("-")
    return (
        db.query(Receipt)
        .filter(
            Receipt.business_id == business_id,
            Receipt.status == "done",
            extract("year", Receipt.receipt_date) == int(year),
            extract("month", Receipt.receipt_date) == int(mon),
        )
        .order_by(Receipt.receipt_date)
        .all()
    )


def _generate_pdf(receipts: list[Receipt], month: str, business: Business) -> str:
    """Generate a simple PDF summary for the given receipts."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"report_{month}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(
        Paragraph(f"Belegbericht - {business.name} - {month}", styles["Title"])
    )
    elements.append(Spacer(1, 6 * mm))

    # Table header
    table_data = [["Nr", "Datum", "Lieferant", "Betrag (BGN)", "MwSt (BGN)", "Netto (BGN)"]]

    total_sum = Decimal("0")
    vat_sum = Decimal("0")

    for idx, r in enumerate(receipts, start=1):
        amount = r.total_amount or Decimal("0")
        vat = r.vat_amount or Decimal("0")
        netto = amount - vat
        total_sum += amount
        vat_sum += vat
        table_data.append([
            str(idx),
            r.receipt_date.strftime("%d.%m.%Y") if r.receipt_date else "",
            r.supplier_name or "",
            f"{amount:.2f}",
            f"{vat:.2f}",
            f"{netto:.2f}",
        ])

    netto_sum = total_sum - vat_sum
    table_data.append(["", "", "Summe", f"{total_sum:.2f}", f"{vat_sum:.2f}", f"{netto_sum:.2f}"])

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E1F2")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    elements.append(table)

    doc.build(elements)
    return filepath


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/preview", response_model=PreviewOut)
def preview_report(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a summary of receipts for the given month (preview before sending)."""
    receipts = _get_receipts_for_month(db, current_user.business_id, month)

    total = sum((r.total_amount or Decimal("0")) for r in receipts)
    vat = sum((r.vat_amount or Decimal("0")) for r in receipts)
    netto = total - vat

    return PreviewOut(
        month=month,
        receipt_count=len(receipts),
        total_sum=float(total),
        vat_sum=float(vat),
        netto_sum=float(netto),
    )


@router.post("/send", response_model=SendResponse)
def send_report(
    body: SendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate Excel + PDF for the month and record the report (email sending is a stub)."""
    business = db.query(Business).filter(Business.id == current_user.business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    if not business.accountant_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No accountant email configured. Update business settings first.",
        )

    receipts = _get_receipts_for_month(db, current_user.business_id, body.month)
    if not receipts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No completed receipts found for {body.month}",
        )

    # Generate files
    excel_path = generate_excel(receipts, body.month)
    pdf_path = _generate_pdf(receipts, body.month, business)

    total = sum((r.total_amount or Decimal("0")) for r in receipts)

    # Record report
    report = MonthlyReport(
        business_id=current_user.business_id,
        sent_by=current_user.id,
        month=body.month,
        excel_path=excel_path,
        pdf_path=pdf_path,
        sent_at=datetime.datetime.utcnow(),
        sent_to_email=business.accountant_email,
        receipt_count=len(receipts),
        total_sum=total,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # TODO: actually send email via aiosmtplib (stub for prototype)

    return SendResponse(
        message=f"Report for {body.month} generated. Email to {business.accountant_email} is queued.",
        report_id=report.id,
        excel_path=excel_path,
        pdf_path=pdf_path,
    )


@router.get("/", response_model=list[ReportOut])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all sent reports for the current user's business."""
    reports = (
        db.query(MonthlyReport)
        .filter(MonthlyReport.business_id == current_user.business_id)
        .order_by(MonthlyReport.sent_at.desc())
        .all()
    )
    return reports
