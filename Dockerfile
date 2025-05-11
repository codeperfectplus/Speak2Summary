FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and set the user
RUN groupadd -r celery && useradd -r -g celery celery

# Copy the rest of the app
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port (Flask)
EXPOSE 5000
