# AI Carousel Generator

Converts a YouTube video into an Instagram-style carousel post using an AI pipeline.

## What it does

1. Fetches the YouTube video transcript
2. Plans a carousel structure (Hook → Problem → Insight → Support → Example → CTA)
3. Generates slide copy (title + body, max 20 words) with validation and auto-retry
4. Generates a caption, hashtags, and CTA
5. Scores carousel quality via LLM self-evaluation
6. Renders 1080×1350 PNG slide images using Pillow

## Quickstart

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env         # add your OPENAI_API_KEY
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`.

## Generate a carousel

```bash
curl -X POST http://localhost:8000/generate-carousel \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.youtube.com/watch?v=EXAMPLE", "slide_count": 6, "tone": "educational"}'
```

`tone` options: `educational` | `motivational` | `promotional`

Generated slide images are saved to `backend/output/`.

## Run with Docker

```bash
cd backend
docker build -t ai-carousel-generator .
docker run -p 8080:8080 --env-file .env ai-carousel-generator
```

## Project structure

```
backend/
├── main.py            # FastAPI app and route handlers
├── pipeline/          # Sequential AI pipeline stages
│   ├── transcript.py  # YouTube transcript retrieval
│   ├── planner.py     # Carousel structure planning
│   ├── slide_writer.py
│   ├── caption_writer.py
│   ├── renderer.py    # Pillow image generation
│   └── validator.py   # Validation + retry logic
├── prompts/           # LLM prompt templates (edit here to tune outputs)
│   ├── planner_prompt.py
│   ├── slide_prompt.py
│   └── caption_prompt.py
└── output/            # Generated slide images (git-ignored)
```

## Environment variables

See `backend/.env.example` for all configuration options.
