# Minimal Dockerfile for Streamlit app
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Port used by many PaaS (Cloud Run etc.)
ENV PORT=8080
EXPOSE 8080

CMD ["streamlit", "run", "vision.py", "--server.port=8080", "--server.address=0.0.0.0"]
