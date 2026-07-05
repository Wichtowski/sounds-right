FROM ghcr.io/astral-sh/uv:python3.12-bookworm

# Install ffmpeg in the worker image
RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY . /workspace
