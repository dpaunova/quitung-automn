from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ReceiptOut(BaseModel):
    id: int
    business_id: int
    uploaded_by: int
    photo_path: str
    photo_url: str | None = None
    status: str
    receipt_date: datetime | None = None
    total_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    supplier_name: str | None = None
    receipt_number: str | None = None
    raw_ocr_text: str | None = None
    field_confidence: dict | None = None
    is_corrected: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReceiptUpdate(BaseModel):
    receipt_date: datetime | None = None
    total_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    supplier_name: str | None = None
    receipt_number: str | None = None


class ReceiptUploadResponse(BaseModel):
    id: int
    status: str
    message: str
