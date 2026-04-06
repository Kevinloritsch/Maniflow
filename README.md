# Maniflow

## Setup

- Run `npm i`
- Run `docker compose up --build` to download
- Run `docker compose up --build web` to setup localhost:3000
- If this fails, and `docker --version` does not work, install docker locally (https://www.docker.com/products/docker-desktop/). Make sure Docker is running locally before running the command.
- Afterwards, in main development, use `docker compose up manim` and `npm run dev`.

To run backend
- Go to ai_pipeline directory and run `uvicorn new_video_analyze:app --reload --port 8000`

## Env

The following env variables are required for this project.

- `MANIM_API_URL=`
