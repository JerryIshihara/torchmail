FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY src/search_engine/requirements.txt /tmp/search_requirements.txt
COPY src/backend/requirements.txt /tmp/backend_requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r /tmp/search_requirements.txt \
  && pip install --no-cache-dir -r /tmp/backend_requirements.txt

COPY src /app/src
COPY .env.example /app/.env.example

EXPOSE 8000

CMD ["sh", "-c", "uvicorn src.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
