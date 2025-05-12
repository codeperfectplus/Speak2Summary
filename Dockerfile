FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies (ffmpeg, gcc for building some Python packages)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt .
# update pip    
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and set the user
RUN groupadd -r celery && useradd -r -g celery celery

# Copy the rest of the app
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port for Flask
EXPOSE 5000
