FROM python:3.11-slim

WORKDIR /app

# Cai dependencies truoc de tan dung cache
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Giu nguyen cau truc backend/ de khop startCommand "cd backend && uvicorn"
COPY backend/ ./backend/

WORKDIR /app/backend

# Railway cung cap bien $PORT luc runtime
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
