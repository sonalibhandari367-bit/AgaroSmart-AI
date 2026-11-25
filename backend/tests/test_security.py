from starlette.testclient import TestClient
from app.main import app


def test_anonymous_boundaries_and_untrusted_ids():
    with TestClient(app) as client:
        assert client.post("/api/admin/imports").status_code == 401
        assert client.post("/api/admin/imports", headers={"X-Admin-Token": "wrong"}).status_code == 401
        assert client.get("/api/recommendations/1").status_code == 404
        payload = dict(nitrogen=80, phosphorus=45, potassium=40, ph=6.5,
                       temperature_c=24, humidity_pct=72, rainfall_mm=100)
        assert client.post("/api/recommendations", json=payload).status_code == 200
        assert client.post("/api/recommendations", json=dict(payload, user_id=1)).status_code == 422
        assert client.post("/api/recommendations", json=dict(payload, recommendation_id=1)).status_code == 422


def test_upload_requires_csv_extension_and_content_type():
    with TestClient(app) as client:
        response = client.post("/api/admin/imports", headers={"X-Admin-Token": "test-admin-token"},
                               files={"file": ("payload.html", b"<script>alert(1)</script>", "text/csv")})
        assert response.status_code == 415
