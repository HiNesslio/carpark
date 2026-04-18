# Railway Deployment - Macau Carpark API
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    ca-certificates \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and Chromium
RUN pip install --no-cache-dir playwright \
    && playwright install chromium \
    && playwright install-deps

# Expose port
EXPOSE 8080

# Use ENTRYPOINT with explicit shell for PORT variable
ENTRYPOINT ["/bin/sh", "-c", "exec gunicorn app:app --bind 0.0.0.0:${PORT:-8080}"]