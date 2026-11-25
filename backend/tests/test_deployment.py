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
