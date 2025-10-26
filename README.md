# Toys Catalog API (FastAPI + SQLAlchemy + Alembic + JWT)

This project implements the **Toys Catalog API** per the provided Technical Specification (TZ).

## Quick Start

1. **Create & fill environment file**

```bash
cp .env.example .env
# Edit values as needed
```

2. **Create virtual env & install deps**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Run migrations**

```bash
alembic upgrade head
```

> If you change models, run `alembic revision --autogenerate -m "msg"` then `alembic upgrade head`.

4. **Start API**

```bash
make run
# or
uvicorn app.main:app --reload
```

### Default API Info

- Base URL: `/api/v1`
- OpenAPI: `/api/v1/docs`
- Health: `/api/v1/system/health`

### Notes

- BaseResponse format is unified for all endpoints.
- Language: pass `?lang=uz|ru` (default: `uz`).
- Pagination: `?limit=20&offset=0` (+ filters/sort).
- RBAC: roles `user`, `admin`. See `routers/*` for guards.
- PDF receipts generated with ReportLab (simple layout).
- Email sending is simulated to console by default. Hook `utils/emailer.py` for SMTP if needed.
