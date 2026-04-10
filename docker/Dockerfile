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

COPY requirements.txt ./

RUN --mount=type=cache, target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# RUN --mount=type=cache, target=/root/.cache/ms-playwright \
#     playwright install chromium

WORKDIR /app

COPY server.py ./
#driver.py
# Files needed for scraping and rag compilation. Uncomment during development.
#COPY backend/ai_pipeline/rag/rag.py        ./
#COPY backend/ai_pipeline/rag/scraping      ./


# Google Drive credentials. Uncomment during development.
#COPY credentials/credentials.json token.json ./

EXPOSE 5000
CMD ["python", "server.py"]