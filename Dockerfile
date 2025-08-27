# Use the official Python 3.11 slim image as the base
FROM python:3.11

# Install system dependencies required for PyAudio and other packages
RUN apt-get update && apt-get install -y \
    gcc \                # C compiler for building Python packages \
    g++ \                # C++ compiler \
    portaudio19-dev \    # Required for PyAudio \
    python3-dev \        # Python headers for building some packages \
    pkg-config \         # Helper for compiling C extensions \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt cache to reduce image size

# Set the working directory inside the container
WORKDIR /app

# Copy the Python dependencies file into the container
COPY requirements.txt .

# Install uv (fast Python package installer) and all Python dependencies
RUN pip install uv \
    && uv pip install --system -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the default port for the application (Cloud Run will override this)
ENV PORT=8000

# Expose the port for local development and container linking
EXPOSE 8000

# Start the FastAPI app with Uvicorn, using the PORT environment variable and 4 workers
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 4