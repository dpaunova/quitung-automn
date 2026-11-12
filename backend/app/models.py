import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    eik_bulstat = Column(String(20), nullable=False, unique=True)
    vat_number = Column(String(20), nullable=True)
    accountant_email = Column(String(255), nullable=True)
    accountant_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, server_default=func.now())

    users = relationship("User", back_populates="business")
    receipts = relationship("Receipt", back_populates="business")
    reports = relationship("MonthlyReport", back_populates="business")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="staff")  # admin / staff
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, server_default=func.now())

    business = relationship("Business", back_populates="users")
    receipts = relationship("Receipt", back_populates="uploader")
    reports = relationship("MonthlyReport", back_populates="sender")


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    photo_path = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default="processing")  # processing / done / failed
    receipt_date = Column(DateTime, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)
    vat_amount = Column(Numeric(10, 2), nullable=True)
    supplier_name = Column(String(255), nullable=True)
    receipt_number = Column(String(100), nullable=True)
    raw_ocr_text = Column(Text, nullable=True)
    field_confidence = Column(JSON, nullable=True)
    is_corrected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, server_default=func.now())

    business = relationship("Business", back_populates="receipts")
    uploader = relationship("User", back_populates="receipts")


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    sent_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    month = Column(String(7), nullable=False)  # YYYY-MM
    excel_path = Column(String(500), nullable=True)
    pdf_path = Column(String(500), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    sent_to_email = Column(String(255), nullable=True)
    receipt_count = Column(Integer, default=0)
    total_sum = Column(Numeric(12, 2), default=0)

    business = relationship("Business", back_populates="reports")
    sender = relationship("User", back_populates="reports")
