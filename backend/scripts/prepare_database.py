"""Run from backend/ once before deploying against a new or updated database."""
from alembic import command
from alembic.config import Config
from app.services.seed import seed_catalog


if __name__ == "__main__":
    command.upgrade(Config("alembic.ini"), "head")
    seed_catalog()
    print("Database migrated and catalog seeded.")
