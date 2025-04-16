FROM python:3.10-slim

WORKDIR /

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the application
COPY bot/ ./bot/
COPY config/ ./config/
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/bot

# Expose the port the app runs on
EXPOSE 8084

# Command to run the application
CMD ["python", "bot/bot.py"] 
