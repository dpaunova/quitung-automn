from tests.conftest import auth_header, register_user


class TestGetBusiness:
    def test_get_business(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.get("/api/business/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test EOOD"
        assert data["eik_bulstat"] == "123456789"
        assert data["vat_number"] == "BG123456789"

    def test_get_business_no_auth(self, client):
        resp = client.get("/api/business/")
        assert resp.status_code == 401


class TestUpdateBusiness:
    def test_update_accountant_info(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.patch(
            "/api/business/",
            json={
                "accountant_email": "accountant@example.com",
                "accountant_name": "Maria Ivanova",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["accountant_email"] == "accountant@example.com"
        assert data["accountant_name"] == "Maria Ivanova"

    def test_update_partial(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.patch(
            "/api/business/",
            json={"name": "Updated EOOD"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated EOOD"
        assert resp.json()["eik_bulstat"] == "123456789"

    def test_update_requires_admin(self, client):
        register_user(client)
        headers = auth_header(client)
        # invite a staff user
        client.post(
            "/api/auth/invite",
            json={
                "email": "staff@example.com",
                "name": "Staff User",
                "role": "staff",
                "temp_password": "staffpass",
            },
            headers=headers,
        )
        staff_headers = auth_header(client, email="staff@example.com", password="staffpass")
        resp = client.patch(
            "/api/business/",
            json={"name": "Hacked"},
            headers=staff_headers,
        )
        assert resp.status_code == 403
