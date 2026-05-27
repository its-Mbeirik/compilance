FROM python:3.11-slim

WORKDIR /app

# System deps for pdfplumber, weasyprint, psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7 \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-ara \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU (suffisant pour BGE-M3 en dev)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
