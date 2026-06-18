FROM python:3.11-slim

WORKDIR /app

# Cai dependencies truoc de tan dung cache
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy toan bo source backend vao /app
COPY backend/ ./

# Railway cung cap bien $PORT luc runtime
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
