FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-jpn \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY app/ ./app/

WORKDIR /srv/app

ENV PORT=8080
EXPOSE 8080

CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 0 app:app
