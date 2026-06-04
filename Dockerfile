FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=.

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

# Expose port
EXPOSE 8080

# Start server
CMD ["python3", "src/server.py"]
