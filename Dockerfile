# Blender Render Environment
# Usage: docker build -t fact-agent-blender -f Dockerfile.blender .
#        docker run --rm -v $(pwd)/output:/output fact-agent-blender python render.py

FROM ubuntu:22.04

# Install Blender and dependencies
ARG BLENDER_VERSION=4.0.2
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    wget \
    python3 \
    python3-pip \
    libgl1-mesa-glx \
    libxi6 \
    libxxf86vm1 \
    libxrender1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Blender
RUN wget -q "https://download.blender.org/release/Blender4.0/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && tar -xf "blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && mv "blender-${BLENDER_VERSION}-linux-x64" /opt/blender \
    && ln -s /opt/blender/blender /usr/local/bin/blender \
    && rm "blender-${BLENDER_VERSION}-linux-x64.tar.xz"

# Python dependencies for the render pipeline
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Working directory
WORKDIR /workspace

# Default entrypoint
ENTRYPOINT ["blender", "--background", "--python"]