import io

from PIL import Image

from tests.conftest import auth_header, register_user


def _make_test_image(fmt="JPEG"):
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf


class TestUploadReceipt:
    def test_upload_jpeg(self, client):
        register_user(client)
        headers = auth_header(client)
        buf = _make_test_image()
        resp = client.post(
            "/api/receipts/",
            files={"file": ("receipt.jpg", buf, "image/jpeg")},
            headers=headers,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "done"
        assert "id" in data

    def test_upload_png(self, client):
        register_user(client)
        headers = auth_header(client)
        buf = _make_test_image("PNG")
        resp = client.post(
            "/api/receipts/",
            files={"file": ("receipt.png", buf, "image/png")},
            headers=headers,
        )
        assert resp.status_code == 202

    def test_upload_invalid_type(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.post(
            "/api/receipts/",
            files={"file": ("doc.pdf", io.BytesIO(b"fake"), "application/pdf")},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_upload_requires_auth(self, client):
        buf = _make_test_image()
        resp = client.post(
            "/api/receipts/",
            files={"file": ("receipt.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 401


class TestListReceipts:
    def test_list_empty(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.get("/api/receipts/", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_upload(self, client):
        register_user(client)
        headers = auth_header(client)
        buf = _make_test_image()
        client.post(
            "/api/receipts/",
            files={"file": ("r.jpg", buf, "image/jpeg")},
            headers=headers,
        )
        resp = client.get("/api/receipts/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetReceipt:
    def test_get_existing(self, client):
        register_user(client)
        headers = auth_header(client)
        buf = _make_test_image()
        upload = client.post(
            "/api/receipts/",
            files={"file": ("r.jpg", buf, "image/jpeg")},
            headers=headers,
        )
        rid = upload.json()["id"]
        resp = client.get(f"/api/receipts/{rid}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == rid

    def test_get_nonexistent(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.get("/api/receipts/9999", headers=headers)
        assert resp.status_code == 404


class TestUpdateReceipt:
    def test_update_fields(self, client):
        register_user(client)
        headers = auth_header(client)
        buf = _make_test_image()
        upload = client.post(
            "/api/receipts/",
            files={"file": ("r.jpg", buf, "image/jpeg")},
            headers=headers,
        )
        rid = upload.json()["id"]
        resp = client.patch(
            f"/api/receipts/{rid}",
            json={"supplier_name": "Lidl", "total_amount": 42.50},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["supplier_name"] == "Lidl"
        assert data["is_corrected"] is True


class TestDeleteReceipt:
    def test_admin_can_delete(self, client):
        register_user(client)
        headers = auth_header(client)
        buf = _make_test_image()
        upload = client.post(
            "/api/receipts/",
            files={"file": ("r.jpg", buf, "image/jpeg")},
            headers=headers,
        )
        rid = upload.json()["id"]
        resp = client.delete(f"/api/receipts/{rid}", headers=headers)
        assert resp.status_code == 204

        resp2 = client.get(f"/api/receipts/{rid}", headers=headers)
        assert resp2.status_code == 404
