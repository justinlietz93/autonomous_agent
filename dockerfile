# Use an official Python runtime as a parent image.
FROM python:3.9-slim

# Install system dependencies including X11 for screenshots and editors
RUN apt-get update && apt-get install -y \
    x11-apps \
    x11-utils \
    xvfb \
    gedit \
    nano \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual display for X11 applications
ENV DISPLAY=:99

# Set the working directory in the container.
WORKDIR /app

# Copy setup.py first for better caching
COPY setup.py /app/

# Install package and dependencies
RUN pip install --no-cache-dir -e .

# Copy the rest of your code into the container.
COPY . /app

# Set up virtual framebuffer for X11
RUN echo 'Xvfb :99 -screen 0 1024x768x16 &' > /docker-entrypoint.sh && \
    echo 'python main_autonomous.py --provider deepseek-r1-32b_ollama --prompt demo_prompt' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Make sure files are accessible
RUN chmod -R 755 /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the entrypoint script
CMD ["/bin/bash", "/docker-entrypoint.sh"]
