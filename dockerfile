# Use the latest Ubuntu as our base
FROM ubuntu:latest

# Install Python, pip, venv, Xvfb (headless X), and xauth (for X authority tokens)
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv xvfb xauth && \
    rm -rf /var/lib/apt/lists/*

# Create a virtual environment (named /venv)
RUN python3 -m venv /venv

# Ensure the container uses /venv binaries (python, pip) by default
ENV PATH="/venv/bin:$PATH"

# Copy the project archive into the container (make sure project.tar is in your build context)
COPY project.tar /tmp/project.tar

# Unpack the project archive to /fake_root
RUN mkdir -p /fake_root
RUN tar -xf /tmp/project.tar -C /fake_root && rm /tmp/project.tar

# Install project dependencies into the venv
RUN pip install --no-cache-dir -r /fake_root/requirements.txt

# Set DISPLAY to :99 for Xvfb
ENV DISPLAY=:99

# The final command:
# 1) Start Xvfb on :99
# 2) Use xauth to generate a .Xauthority file for the display
# 3) Keep container alive with tail
CMD ["/bin/bash", "-c", "\
    Xvfb :99 -screen 0 1024x768x24 & \
    sleep 2 && \
    xauth generate :99 . trusted && \
    tail -f /dev/null \
"]
