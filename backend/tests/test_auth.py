from tests.conftest import auth_header, login_user, register_user


class TestRegister:
    def test_register_success(self, client):
        resp = register_user(client)
        assert resp.status_code == 201
        assert resp.json()["message"] == "Registration successful. You can now log in."

    def test_register_duplicate_email(self, client):
        register_user(client)
        resp = register_user(client, eik_bulstat="999999999")
        assert resp.status_code == 409
        assert "Email already registered" in resp.json()["detail"]

    def test_register_duplicate_eik(self, client):
        register_user(client)
        resp = register_user(client, email="other@example.com")
        assert resp.status_code == 409
        assert "EIK/Bulstat" in resp.json()["detail"]


class TestLogin:
    def test_login_success(self, client):
        register_user(client)
        resp = login_user(client)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "admin"

    def test_login_wrong_password(self, client):
        register_user(client)
        resp = login_user(client, password="wrong")
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = login_user(client, email="nope@example.com")
        assert resp.status_code == 401


class TestInvite:
    def test_invite_success(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.post(
            "/api/auth/invite",
            json={
                "email": "staff@example.com",
                "name": "Staff User",
                "role": "staff",
                "temp_password": "temp123",
            },
            headers=headers,
        )
        assert resp.status_code == 201

        resp2 = login_user(client, "staff@example.com", "temp123")
        assert resp2.status_code == 200
        assert resp2.json()["user"]["role"] == "staff"

    def test_invite_requires_admin(self, client):
        register_user(client)
        headers = auth_header(client)
        client.post(
            "/api/auth/invite",
            json={
                "email": "staff@example.com",
                "name": "Staff",
                "role": "staff",
                "temp_password": "temp123",
            },
            headers=headers,
        )
        staff_headers = auth_header(client, "staff@example.com", "temp123")
        resp = client.post(
            "/api/auth/invite",
            json={
                "email": "another@example.com",
                "name": "Another",
                "role": "staff",
                "temp_password": "temp123",
            },
            headers=staff_headers,
        )
        assert resp.status_code == 403

    def test_invite_invalid_role(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.post(
            "/api/auth/invite",
            json={
                "email": "bad@example.com",
                "name": "Bad",
                "role": "superuser",
                "temp_password": "temp123",
            },
            headers=headers,
        )
        assert resp.status_code == 400

    def test_invite_duplicate_email(self, client):
        register_user(client)
        headers = auth_header(client)
        resp = client.post(
            "/api/auth/invite",
            json={
                "email": "test@example.com",
                "name": "Dup",
                "role": "staff",
                "temp_password": "temp123",
            },
            headers=headers,
        )
        assert resp.status_code == 409
