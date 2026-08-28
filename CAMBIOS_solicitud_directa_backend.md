# ── Python ────────────────────────────────────────────────────────────────────
__pycache__/
*.pyc
*.pyo
*.pyd
*.pyw

# ── Entornos virtuales ────────────────────────────────────────────────────────
venv/
.venv/
env/
ENV/

# ── Variables de entorno / credenciales ───────────────────────────────────────
.env
.env.*
!.env.example
*.pem
*.key
secrets.json
credentials.json

# ── Base de datos local (restos SQLite si los hubiera) ────────────────────────
*.db
*.sqlite
*.sqlite3

# ── Logs ──────────────────────────────────────────────────────────────────────
*.log
logs/

# ── Exports generados localmente ─────────────────────────────────────────────
*.xlsx
*.xls
*.csv

# ── Tests y cobertura ─────────────────────────────────────────────────────────
.pytest_cache/
htmlcov/
.coverage
coverage.xml

# ── Builds y distribución ─────────────────────────────────────────────────────
dist/
build/
*.egg-info/

# ── IDEs ──────────────────────────────────────────────────────────────────────
.vscode/
.idea/
.cursor/
*.swp
*.swo

# ── Cachés de linters/type-checkers ───────────────────────────────────────────
.mypy_cache/
.ruff_cache/

# ── Sistema operativo ─────────────────────────────────────────────────────────
.DS_Store
Thumbs.db
desktop.ini
__MACOSX/

# ── Miscelánea ────────────────────────────────────────────────────────────────
*.bak
*.tmp
*.orig
instance/

# ── Releases y paquetes ───────────────────────────────────────────────────────
releases/
*.zip

# ── Instaladores ──────────────────────────────────────────────────────────────
*.exe
*.msi

# ── PyInstaller (por si se comparte tooling con OrganizadorPrincess) ─────────
*.spec
