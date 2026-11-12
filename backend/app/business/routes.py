from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models import Business, User

router = APIRouter(prefix="/api/business", tags=["business"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class BusinessOut(BaseModel):
    id: int
    name: str
    eik_bulstat: str
    vat_number: str | None = None
    accountant_email: str | None = None
    accountant_name: str | None = None

    model_config = {"from_attributes": True}


class BusinessUpdate(BaseModel):
    name: str | None = None
    vat_number: str | None = None
    accountant_email: EmailStr | None = None
    accountant_name: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=BusinessOut)
def get_business(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's business."""
    business = db.query(Business).filter(Business.id == current_user.business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business


@router.patch("/", response_model=BusinessOut)
def update_business(
    body: BusinessUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin only: update business fields (accountant info, etc.)."""
    business = db.query(Business).filter(Business.id == admin.business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(business, field, value)

    db.commit()
    db.refresh(business)
    return business
