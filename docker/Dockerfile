FROM manimcommunity/manim:v0.18.0

USER root

COPY docker/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY docker/server.py ./
#driver.py

# files needed for rag and scraping, uncomment during dev
COPY backend/ai_pipeline/rag/rag.py                            ./
COPY backend/ai_pipeline/rag/scraping/                ./scraping/


# google drive credentials (?)
#COPY credentials/credentials.json token.json ./

EXPOSE 5000

CMD ["python", "server.py"]