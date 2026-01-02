FROM python:3.10-slim

# Install system dependencies including tshark for packet capture
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y tshark gcc libpcap-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
