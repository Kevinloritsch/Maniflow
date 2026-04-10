FROM manimcommunity/manim:v0.18.0

USER root

RUN pip install --no-cache-dir flask

WORKDIR /app

COPY server.py ./

EXPOSE 5000

CMD ["python", "server.py"]