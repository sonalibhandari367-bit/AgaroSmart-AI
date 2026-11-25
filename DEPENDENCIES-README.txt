This ZIP uses ZIP_STORED (no compression).
Includes installed frontend/node_modules, backend/.venv and Windows x64 Python/Node runtimes.
Secrets (.env files), local databases, logs and Git metadata are excluded.
Copy .env.example files and supply your own settings as needed.
Dependencies are Windows-specific; install from manifests for Linux/Vercel.
Virtual environments contain absolute paths; do not rely on the bundled venv launcher after moving.
To run backend from PowerShell in the extracted backend folder:
$env:PYTHONPATH = "$PWD\.venv\Lib\site-packages"
$env:DATABASE_URL = "sqlite:///./agrosmart.db"
& ..\runtimes\python\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
To run frontend from a second PowerShell in the extracted frontend folder:
& ..\runtimes\node\node.exe node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173
Open http://localhost:5173 . Hosted deployment still needs external PostgreSQL.
