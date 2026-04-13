# ── Stage 1: Base image ──────────────────────────────────────────────────────
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed by mysql-connector and bcrypt
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API source code
COPY API.py .

# Expose the Flask port
EXPOSE 5000

# Environment variables (override these at runtime or in docker-compose)
ENV DB_HOST=db
ENV DB_USER=root
ENV DB_PASSWORD=admin
ENV DB_NAME=school_db
ENV JWT_SECRET=change_this_in_production
ENV PORT=5000

# Run the API
CMD ["python", "API.py"]
