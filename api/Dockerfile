FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app

# Expose the port uvicorn will run on (8080 is Google Cloud standard)
EXPOSE 8080

# Command to run the application
# Use PORT environment variable (Google Cloud sets this), default to 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]