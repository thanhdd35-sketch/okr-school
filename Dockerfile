FROM python:3.11-slim

WORKDIR /app

# Cai dependencies truoc de tan dung cache
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Giu nguyen cau truc backend/
COPY backend/ ./backend/

WORKDIR /app/backend

# $PORT do Railway cung cap; default 8000 neu thieu (tranh loi bind -> 502)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
