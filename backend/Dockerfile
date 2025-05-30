FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including SSL certificates
RUN apt-get update && \
    apt-get install -y curl ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install certificates
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir certifi

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 