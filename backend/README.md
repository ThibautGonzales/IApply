# IApply backend

FastAPI application.

## Run locally (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
fastapi dev app/main.py        # http://localhost:8000/health and /docs
```

## Run the tests

```bash
cd backend
python -m pytest
```
