FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y cron \
    && service cron start \
    && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN touch /var/log/cron.log
RUN echo "* * * * * root echo 'Cron is working!' >> /var/log/cron.log 2>&1" > /etc/cron.d/example-cron-job
RUN chmod 0644 /etc/cron.d/example-cron-job

RUN echo '#!/bin/bash\n\
service cron start\n\
echo "Cron service started"\n\
# Выводим логи для отладки\n\
tail -f /var/log/cron.log\n\
' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Copy the application
COPY api/ .
COPY config/ ./config/
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8083

# Command to run the application
CMD ["python", "main.py"] 
