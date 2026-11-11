import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from PIL import Image
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.config import settings
from app.database import get_db
from app.models import Receipt, User
from app.receipts.schemas import ReceiptOut, ReceiptUpdate, ReceiptUploadResponse

router = APIRouter(prefix="/api/receipts", tags=["receipts"])

MAX_WIDTH = 1600


def _compress_and_save(upload: UploadFile, dest_path: str) -> None:
    """Resize image to MAX_WIDTH (keeping aspect ratio) and save as JPEG."""
    img = Image.open(upload.file)
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_size = (MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    # Convert RGBA to RGB for JPEG
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(dest_path, "JPEG", quality=85)


def _receipt_to_out(receipt: Receipt) -> ReceiptOut:
    """Convert a Receipt ORM object to a ReceiptOut schema with photo_url."""
    data = ReceiptOut.model_validate(receipt)
    data.photo_url = f"/uploads/{os.path.basename(receipt.photo_path)}"
    return data


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=ReceiptUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a receipt photo. Saves a compressed copy and creates a receipt record."""
    # Validate content type
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WebP images are accepted",
        )

    # Validate file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE // (1024*1024)} MB",
        )

    # Save compressed image
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    dest_path = os.path.join(settings.UPLOAD_DIR, filename)

    try:
        _compress_and_save(file, dest_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not process image: {exc}",
        )

    receipt = Receipt(
        business_id=current_user.business_id,
        uploaded_by=current_user.id,
        photo_path=dest_path,
        status="processing",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    # TODO: enqueue ARQ job for OCR/VLM processing
    # For now, mark as done with empty fields (mock)
    if not settings.VLM_ENABLED:
        receipt.status = "done"
        receipt.field_confidence = {}
        db.commit()

    return ReceiptUploadResponse(
        id=receipt.id,
        status=receipt.status,
        message="Receipt uploaded. Processing started.",
    )


@router.get("/", response_model=list[ReceiptOut])
def list_receipts(
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List receipts for the current user's business, optionally filtered by month (YYYY-MM)."""
    query = db.query(Receipt).filter(Receipt.business_id == current_user.business_id)

    if month:
        # Filter by year-month prefix of receipt_date
        year, mon = month.split("-")
        from sqlalchemy import extract

        query = query.filter(
            extract("year", Receipt.receipt_date) == int(year),
            extract("month", Receipt.receipt_date) == int(mon),
        )

    receipts = query.order_by(Receipt.created_at.desc()).all()
    return [_receipt_to_out(r) for r in receipts]


@router.get("/{receipt_id}", response_model=ReceiptOut)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single receipt by ID (must belong to the user's business)."""
    receipt = (
        db.query(Receipt)
        .filter(
            Receipt.id == receipt_id,
            Receipt.business_id == current_user.business_id,
        )
        .first()
    )
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    return _receipt_to_out(receipt)


@router.patch("/{receipt_id}", response_model=ReceiptOut)
def update_receipt(
    receipt_id: int,
    body: ReceiptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update (correct) receipt fields. Sets is_corrected=True."""
    receipt = (
        db.query(Receipt)
        .filter(
            Receipt.id == receipt_id,
            Receipt.business_id == current_user.business_id,
        )
        .first()
    )
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(receipt, field, value)
    receipt.is_corrected = True

    db.commit()
    db.refresh(receipt)
    return _receipt_to_out(receipt)


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin only: delete a receipt and its photo file."""
    receipt = (
        db.query(Receipt)
        .filter(
            Receipt.id == receipt_id,
            Receipt.business_id == admin.business_id,
        )
        .first()
    )
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    # Remove photo file
    if receipt.photo_path and os.path.exists(receipt.photo_path):
        os.remove(receipt.photo_path)

    db.delete(receipt)
    db.commit()
