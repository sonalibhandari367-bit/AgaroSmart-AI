import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_agrosmart.db")
os.environ.setdefault("ADMIN_API_TOKEN", "test-admin-token")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
