FROM python:3.12-slim

# Create a non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=.

# Install system dependencies if any, clean up apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/ ./src/
COPY bin/ ./bin/
COPY discover/ ./discover/
COPY doc/ ./doc/
COPY investigations/ ./investigations/
COPY run_simulation.py .
COPY GEMINI.md .
COPY VERSION .

# Set ownership of the application files to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose port
EXPOSE 8080

# Start server
CMD ["python3", "src/server.py"]
