# Use Python 3.11 on Ubuntu 22.04 for stable packages
FROM python:3.11-slim-bullseye

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgtk-3-0 \
    ffmpeg \
    libavcodec58 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for headless operation
ENV OPENCV_IO_ENABLE_OPENEXR=0
ENV QT_QPA_PLATFORM=offscreen
ENV DISPLAY=:99
ENV MPLBACKEND=Agg

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Create necessary directories
RUN mkdir -p uploads results

# Expose port
EXPOSE 8080

# Start the application with startup script
CMD ["./start.sh"]
