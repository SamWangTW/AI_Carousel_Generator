# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered carousel generator that converts YouTube videos into Instagram-style carousel posts. The project is currently in early development — only the system design exists; implementation has not started yet.

## Planned Tech Stack

- **Backend:** Python + FastAPI, deployed via Docker to Google Cloud Run
- **AI:** OpenAI API
- **Transcript:** `youtube-transcript-api`
- **Image Rendering:** Pillow (1080×1350 px slides)
- **Storage:** Local JSON (prototype) → Firestore (production)
- **Frontend:** React Native (Expo) — mobile-first

## Planned Folder Structure

```
AI_Carousel_Generator/
├── backend/
│   ├── main.py                   # FastAPI entry point
│   ├── pipeline/
│   │   ├── transcript.py         # YouTube transcript retrieval
│   │   ├── planner.py            # Carousel structure planning
│   │   ├── slide_writer.py       # Slide copy generation
│   │   ├── caption_writer.py     # Caption + hashtag generation
│   │   ├── renderer.py           # Pillow image rendering
│   │   └── validator.py          # Output validation + retry logic
│   ├── prompts/
│   │   ├── planner_prompt.py     # Prompt template for planning
│   │   ├── slide_prompt.py       # Prompt template for slide copy
│   │   └── caption_prompt.py     # Prompt template for captions
│   ├── output/                   # Generated slide images saved here
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── system_design.md
└── README.md
```

## Commands (once implemented)

```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Run backend locally
uvicorn backend.main:app --reload

# Build Docker image
docker build -t ai-carousel-generator ./backend

# Run Docker container
docker run -p 8080:8080 --env-file backend/.env ai-carousel-generator
```

## Core Architecture

### AI Pipeline (agent-like, sequential)

`POST /generate-carousel` triggers this pipeline:

1. **Transcript** — fetch & clean YouTube captions via `youtube-transcript-api`
2. **Planner** — LLM extracts topics, structures carousel (Hook → Problem → Insight → Support → Example → CTA)
3. **Slide Writer** — LLM generates slide copy (max 20 words per slide body)
4. **Validator** — validates each slide; auto-retries with stricter prompt up to 2 times on failure
5. **Caption Writer** — LLM generates caption, hashtags, and CTA
6. **Quality Scorer** — LLM self-evaluates hook strength, clarity, CTA (1–10 scores)
7. **Renderer** — Pillow renders 1080×1350 PNG slides to `backend/output/`
8. **Storage** — saves project metadata to local JSON (prototype) or Firestore (production)

### Tone System

All generation prompts adapt based on a `tone` parameter: `educational | motivational | promotional`.
Tone instructions live in `backend/pipeline/` modules and are injected at prompt-construction time.

### Prompt Files

All LLM prompt templates live in `backend/prompts/` — keep prompts separated from pipeline logic for easy iteration and version control.

### Validation + Retry Pattern

```python
MAX_RETRIES = 2
for attempt in range(MAX_RETRIES):
    result = generate(prompt)
    if validate(result):
        break
    prompt += "\nIMPORTANT: <stricter constraint>"
```

Apply this pattern consistently across all pipeline stages that produce LLM output.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/generate-carousel` | Full pipeline: URL → slides + caption |
| POST | `/regenerate-slide` | Regenerate a single slide |
| POST | `/regenerate-caption` | Regenerate caption/hashtags only |
| GET | `/projects/{id}` | Retrieve saved project |
| PATCH | `/projects/{id}` | Update project (edits) |
| POST | `/export-carousel` | Export slide images |

## Prototype Scope

**Included:** FastAPI backend, single working endpoint, transcript retrieval, AI pipeline with validation/retry, tone awareness, quality scoring, Pillow rendering, Dockerfile, `.env.example`.

**Excluded (not yet):** Google Cloud deployment, Firestore, authentication, Instagram publishing.
