import os
import uuid
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.config import settings
from app.models import Receipt

# Yellow fill for low-confidence cells
LOW_CONFIDENCE_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
HEADER_FONT = Font(bold=True, size=11)
HEADER_FILL = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
SUM_FONT = Font(bold=True, size=11)

CONFIDENCE_THRESHOLD = 0.85

# Column headers (German accounting terms as used in Bulgarian context)
COLUMNS = [
    "Nr",
    "Datum",
    "Lieferant",
    "Belegnummer",
    "Betrag (BGN)",
    "MwSt (BGN)",
    "Netto (BGN)",
    "Status",
]

# Map column index to confidence field name (0-based, only for data columns)
CONFIDENCE_MAP = {
    1: "receipt_date",
    2: "supplier_name",
    3: "receipt_number",
    4: "total_amount",
    5: "vat_amount",
}


def generate_excel(receipts: list[Receipt], month: str) -> str:
    """
    Generate an Excel report for the given receipts.

    Returns the file path of the generated .xlsx file.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = f"Belege {month}"

    # --- Header row ---
    for col_idx, header in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")

    # --- Data rows ---
    total_sum = Decimal("0")
    vat_sum = Decimal("0")
    netto_sum = Decimal("0")

    for row_idx, receipt in enumerate(receipts, start=2):
        amount = receipt.total_amount or Decimal("0")
        vat = receipt.vat_amount or Decimal("0")
        netto = amount - vat

        total_sum += amount
        vat_sum += vat
        netto_sum += netto

        confidence = receipt.field_confidence or {}

        row_data = [
            row_idx - 1,  # Nr
            receipt.receipt_date.strftime("%d.%m.%Y") if receipt.receipt_date else "",
            receipt.supplier_name or "",
            receipt.receipt_number or "",
            float(amount),
            float(vat),
            float(netto),
            "Korrigiert" if receipt.is_corrected else receipt.status,
        ]

        for col_idx, value in enumerate(row_data):
            cell = ws.cell(row=row_idx, column=col_idx + 1, value=value)

            # Highlight low-confidence cells in yellow
            field_name = CONFIDENCE_MAP.get(col_idx)
            if field_name and field_name in confidence:
                if confidence[field_name] < CONFIDENCE_THRESHOLD:
                    cell.fill = LOW_CONFIDENCE_FILL

    # --- Footer / sums row ---
    sum_row = len(receipts) + 2
    ws.cell(row=sum_row, column=1, value="Summe").font = SUM_FONT
    ws.cell(row=sum_row, column=5, value=float(total_sum)).font = SUM_FONT
    ws.cell(row=sum_row, column=6, value=float(vat_sum)).font = SUM_FONT
    ws.cell(row=sum_row, column=7, value=float(netto_sum)).font = SUM_FONT

    # Auto-fit column widths (approximate)
    for col_idx in range(1, len(COLUMNS) + 1):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = max(
            len(COLUMNS[col_idx - 1]) + 4, 14
        )

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"report_{month}_{uuid.uuid4().hex[:8]}.xlsx"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    wb.save(filepath)

    return filepath
