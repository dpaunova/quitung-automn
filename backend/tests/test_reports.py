import datetime
from decimal import Decimal
from io import BytesIO

from PIL import Image

from app.models import Receipt
from tests.conftest import auth_header, register_user


def _upload_receipt(client, headers):
    """Upload a test receipt image and return its ID."""
    img = Image.new("RGB", (100, 100), color="red")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    resp = client.post(
        "/api/receipts/",
        files={"file": ("test.jpg", buf, "image/jpeg")},
        headers=headers,
    )
    return resp.json()["id"]


def _make_done_receipt(db, business_id, user_id, month="2025-01"):
    """Insert a done receipt directly into the DB for report testing."""
    receipt = Receipt(
        business_id=business_id,
        uploaded_by=user_id,
        photo_path="/fake/path.jpg",
        status="done",
        receipt_date=datetime.datetime(int(month.split("-")[0]), int(month.split("-")[1]), 15),
        total_amount=Decimal("42.50"),
        vat_amount=Decimal("8.50"),
        supplier_name="Test Supplier",
        receipt_number="R-001",
        field_confidence={"total_amount": 0.95, "supplier_name": 0.90},
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


class TestPreviewReport:
    def test_preview_empty_month(self, client, db):
        register_user(client)
        headers = auth_header(client)
        resp = client.get("/api/reports/preview?month=2025-01", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["month"] == "2025-01"
        assert data["receipt_count"] == 0
        assert data["total_sum"] == 0.0

    def test_preview_with_receipts(self, client, db):
        register_user(client)
        headers = auth_header(client)
        token_resp = client.post(
            "/api/auth/login", json={"email": "test@example.com", "password": "secure123"}
        )
        user_id = token_resp.json()["user"]["id"]
        business_id = token_resp.json()["user"]["business_id"]

        _make_done_receipt(db, business_id, user_id, "2025-03")
        _make_done_receipt(db, business_id, user_id, "2025-03")

        resp = client.get("/api/reports/preview?month=2025-03", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["receipt_count"] == 2
        assert data["total_sum"] == 85.0
        assert data["vat_sum"] == 17.0
        assert data["netto_sum"] == 68.0

    def test_preview_invalid_month_format(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.get("/api/reports/preview?month=2025-1", headers=headers)
        assert resp.status_code == 422

    def test_preview_no_auth(self, client):
        resp = client.get("/api/reports/preview?month=2025-01")
        assert resp.status_code == 401


class TestSendReport:
    def test_send_no_accountant_email(self, client, db):
        register_user(client)
        headers = auth_header(client)
        resp = client.post("/api/reports/send", json={"month": "2025-01"}, headers=headers)
        assert resp.status_code == 400
        assert "accountant email" in resp.json()["detail"].lower()

    def test_send_no_receipts(self, client, db):
        register_user(client)
        headers = auth_header(client)
        # set accountant email first
        client.patch(
            "/api/business/",
            json={"accountant_email": "acc@example.com"},
            headers=headers,
        )
        resp = client.post("/api/reports/send", json={"month": "2025-06"}, headers=headers)
        assert resp.status_code == 400
        assert "no completed receipts" in resp.json()["detail"].lower()

    def test_send_success(self, client, db):
        register_user(client)
        headers = auth_header(client)
        token_resp = client.post(
            "/api/auth/login", json={"email": "test@example.com", "password": "secure123"}
        )
        user_id = token_resp.json()["user"]["id"]
        business_id = token_resp.json()["user"]["business_id"]

        # set accountant email
        client.patch(
            "/api/business/",
            json={"accountant_email": "acc@example.com"},
            headers=headers,
        )

        _make_done_receipt(db, business_id, user_id, "2025-04")

        resp = client.post("/api/reports/send", json={"month": "2025-04"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] >= 1
        assert "excel_path" in data
        assert "pdf_path" in data
        assert data["excel_path"].endswith(".xlsx")
        assert data["pdf_path"].endswith(".pdf")

    def test_send_no_auth(self, client):
        resp = client.post("/api/reports/send", json={"month": "2025-01"})
        assert resp.status_code == 401


class TestListReports:
    def test_list_empty(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.get("/api/reports/", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_send(self, client, db):
        register_user(client)
        headers = auth_header(client)
        token_resp = client.post(
            "/api/auth/login", json={"email": "test@example.com", "password": "secure123"}
        )
        user_id = token_resp.json()["user"]["id"]
        business_id = token_resp.json()["user"]["business_id"]

        client.patch(
            "/api/business/",
            json={"accountant_email": "acc@example.com"},
            headers=headers,
        )
        _make_done_receipt(db, business_id, user_id, "2025-05")
        client.post("/api/reports/send", json={"month": "2025-05"}, headers=headers)

        resp = client.get("/api/reports/", headers=headers)
        assert resp.status_code == 200
        reports = resp.json()
        assert len(reports) == 1
        assert reports[0]["month"] == "2025-05"
        assert reports[0]["receipt_count"] == 1
