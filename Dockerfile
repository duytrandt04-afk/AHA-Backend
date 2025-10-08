# Use the official Python 3.11 image as the base
FROM python:3.11

# Install system dependencies required for PyAudio and other packages

# Install system dependencies required for PyAudio and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*
    
# Set the working directory inside the container
WORKDIR /app

# Copy the Python dependencies file into the container
COPY requirements.txt .

# Install uv (fast Python package installer) and all Python dependencies
RUN pip install uv \
    && uv pip install --system -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port for local development and container linking
EXPOSE 8000

# Start the FastAPI app with Uvicorn, using the PORT environment variable and 4 workers
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 4
