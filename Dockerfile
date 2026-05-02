FROM python:3.11-slim

WORKDIR /app

# Python deps first so this layer is cached when only app/ or static/ changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code and the Flutter web build (served by FastAPI's StaticFiles).
COPY app/    ./app/
COPY static/ ./static/

# Railway injects $PORT; default to 8000 for local sanity.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
