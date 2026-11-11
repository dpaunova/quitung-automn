from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin, get_current_user
from app.auth.utils import (
    create_access_token,
    generate_verification_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models import Business, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    business_name: str
    eik_bulstat: str
    vat_number: str | None = None
    user_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class InviteRequest(BaseModel):
    email: EmailStr
    name: str
    role: str = "staff"
    temp_password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    business_id: int
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new business together with its admin user."""
    # Check for duplicate email
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check for duplicate EIK/Bulstat
    if db.query(Business).filter(Business.eik_bulstat == body.eik_bulstat).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Business with this EIK/Bulstat already exists",
        )

    business = Business(
        name=body.business_name,
        eik_bulstat=body.eik_bulstat,
        vat_number=body.vat_number,
    )
    db.add(business)
    db.flush()  # get business.id

    token = generate_verification_token()
    user = User(
        business_id=business.id,
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.user_name,
        role="admin",
        email_verified=True,  # auto-verify for prototype
        verification_token=token,
    )
    db.add(user)
    db.commit()

    return MessageResponse(message="Registration successful. You can now log in.")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    access_token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        user=UserOut.model_validate(user),
    )


@router.post("/invite", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def invite(
    body: InviteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin-only: create a new user for the same business (simplified invite)."""
    if body.role not in ("admin", "staff"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'staff'",
        )

    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        business_id=admin.business_id,
        email=body.email,
        password_hash=hash_password(body.temp_password),
        name=body.name,
        role=body.role,
        email_verified=True,  # auto-verify for prototype
    )
    db.add(user)
    db.commit()

    return MessageResponse(message=f"User {body.email} created successfully.")
