FROM python:3.13-slim

WORKDIR /app

# Install dependencies first so Docker caches this layer when only the code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
