class TestApiRoot:
    def test_api_health(self, client):
        resp = client.get("/api")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "Quitung Automn API"
