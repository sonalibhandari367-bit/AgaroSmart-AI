import pytest
from pydantic import ValidationError
from app.config import Settings


def test_vercel_rejects_local_sqlite():
    with pytest.raises(ValidationError, match="Vercel requires DATABASE_URL"):
        Settings(_env_file=None, vercel=True, database_url="sqlite:///./local.db")


def test_vercel_accepts_postgres():
    settings = Settings(_env_file=None, vercel=True,
                        database_url="postgresql+psycopg://user:pass@db.example/app")
    assert settings.vercel


def test_vercel_normalizes_postgres_scheme():
    settings = Settings(_env_file=None, vercel=True,
                        database_url="postgres://user:pass@db.example/app")
    assert settings.database_url == "postgresql+psycopg://user:pass@db.example/app"


def test_vercel_allows_unset_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None, vercel=True)
    assert settings.database_url == ""


def test_stateless_endpoints_work_without_database():
    from fastapi.testclient import TestClient
    from app import main
    from app.database import get_db

    def no_db():
        yield None

    main.app.dependency_overrides[get_db] = no_db
    try:
        client = TestClient(main.app)
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok", "database": "catalog_only"}

        crops = client.get("/api/crops")
        assert crops.status_code == 200
        assert crops.json()["count"] == 22

        rec = client.post("/api/recommendations", json={
            "nitrogen": 80, "phosphorus": 45, "potassium": 40, "ph": 6.5,
            "temperature_c": 24, "humidity_pct": 72, "rainfall_mm": 100
        })
        assert rec.status_code == 200
        assert len(rec.json()["results"]) == 5
    finally:
        main.app.dependency_overrides.clear()


def test_vercel_entrypoint_preserves_api():
    from index import app
    assert "/api/recommendations" in {route.path for route in app.routes}


def test_hosted_lifespan_does_not_write_schema(monkeypatch):
    import asyncio
    from unittest.mock import Mock
    from app import main

    monkeypatch.setattr(main.settings, "vercel", True)
    create = Mock()
    seed = Mock()
    monkeypatch.setattr(main.Base.metadata, "create_all", create)
    monkeypatch.setattr(main, "seed_catalog", seed)

    async def start():
        async with main.lifespan(main.app):
            pass

    asyncio.run(start())
    create.assert_not_called()
    seed.assert_not_called()
