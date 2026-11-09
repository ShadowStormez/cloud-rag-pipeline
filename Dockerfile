
FROM python:3.12-slim

WORKDIR /app

# Improve Python behavior in containers
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Fetch documentation and populate Chroma before starting FastAPI
CMD ["sh", "-c", "python update_docs.py && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
