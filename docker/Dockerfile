FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libcairo2-dev \
    libpango1.0-dev \
    pkg-config \
    python3-dev \
    gcc \
    texlive-full \
    && rm -rf /var/lib/apt/lists/*

RUN pip install manim flask 
# google-api-python-client google-auth-httplib2 google-auth-oauthlib

WORKDIR /app
COPY server.py ./
# drive.py credentials.json token.json ./

EXPOSE 5000
CMD ["python", "server.py"]