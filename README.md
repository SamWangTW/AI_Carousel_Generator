# AI Carousel Generator

Converts a YouTube video into a ready-to-post Instagram carousel. Paste a URL, choose a tone, and get back slide images, a caption, hashtags, and a quality score — all in one API call.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | Python 3.10 · FastAPI · Uvicorn |
| AI | OpenAI API (`gpt-4o` / `gpt-4o-mini`) |
| Transcript | `youtube-transcript-api` 1.2.4 |
| Image Rendering | Pillow — 1080 × 1350 px PNG (Instagram portrait) |
| Storage | Local JSON (prototype) |
| Containerisation | Docker |

---

## How to Run Locally

**Prerequisites:** Python 3.10+, an OpenAI API key with billing enabled.

```bash
# 1. Clone and enter the backend directory
git clone <repo-url>
cd AI_Carousel_Generator/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Open .env and set OPENAI_API_KEY and OPENAI_MODEL

# 4. (Required) Export YouTube cookies to bypass bot detection
#    Install the "Get cookies.txt LOCALLY" browser extension,
#    visit youtube.com while logged in, export → save as backend/cookies.txt
#    Then set in .env: YOUTUBE_COOKIES_FILE=cookies.txt

# 5. Start the server
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### Run with Docker

```bash
cd backend
docker build -t ai-carousel-generator .
docker run -p 8080:8080 --env-file .env ai-carousel-generator
```

---

## API Reference

### `POST /generate-carousel`

Full pipeline: YouTube URL → slide images + caption + quality score.

**Request**

```json
{
  "video_url": "https://www.youtube.com/watch?v=iJYhGD96NxA",
  "slide_count": 6,
  "tone": "educational"
}
```

| Field | Type | Default | Options |
|---|---|---|---|
| `video_url` | string | — | Any YouTube URL or bare video ID |
| `slide_count` | int | `6` | `2` – `12` |
| `tone` | string | `"educational"` | `educational` · `motivational` · `promotional` |

**Response**

```json
{
  "project_id": "1b43c1e7-873c-4aed-907b-e523d685a9b4",
  "main_topic": "How to get your first online coaching clients",
  "slides": [
    { "index": 1, "title": "Stop Waiting for Clients", "body": "Most coaches never get clients because they wait to be found. You need a system." },
    { "index": 2, "title": "The Real Problem", "body": "You have the skills. You lack a repeatable outreach process that converts strangers." },
    { "index": 3, "title": "The Fix", "body": "Direct outreach + a clear offer beats passive content every single time." },
    { "index": 4, "title": "What Actually Works", "body": "DM 10 qualified leads per day. Follow up twice. Track everything in a spreadsheet." },
    { "index": 5, "title": "Real Example", "body": "Zach closed his first $3k client in week two using this exact cold-DM script." },
    { "index": 6, "title": "Your Next Step", "body": "Pick one platform. Write your offer. Send 10 DMs today. Start now." }
  ],
  "caption": "Most coaches are broke because they're waiting to be discovered. Here's the outreach system that generated $3M in coaching revenue 👇",
  "hashtags": ["#onlinecoaching", "#coachingbusiness", "#clientattraction", "#digitalcoach", "#growyourbusiness"],
  "cta": "Save this post and send your first DM today.",
  "quality_score": {
    "hook_strength": 8,
    "content_clarity": 9,
    "cta_effectiveness": 8,
    "overall": 8.3
  },
  "slide_image_urls": [
    "/output/1b43c1e7-.../slide_1.png",
    "/output/1b43c1e7-.../slide_2.png"
  ]
}
```

### Other Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/regenerate-slide` | Regenerate a single slide by index |
| `POST` | `/regenerate-caption` | Regenerate caption, hashtags, and CTA |
| `GET` | `/projects/{id}` | Retrieve a saved project |
| `PATCH` | `/projects/{id}` | Edit slides, caption, hashtags, or CTA |
| `POST` | `/export-carousel` | Get all slide image URLs for download |

---

## Architecture

```
POST /generate-carousel
        │
        ▼
┌─────────────────┐
│   1. Transcript │  youtube-transcript-api fetches & cleans captions
└────────┬────────┘
         │ clean text
         ▼
┌─────────────────┐
│   2. Planner    │  LLM structures carousel: Hook → Problem → Insight
└────────┬────────┘  → Support → Example → CTA
         │ slide plan [{index, role, idea}, ...]
         ▼
┌──────────────────────┐
│   3. Slide Writer    │  LLM writes title + body (max 20 words) per slide
│   + Validator/Retry  │  Validates each slide; retries up to 2× with
└────────┬─────────────┘  stricter prompt on failure
         │ validated slides [{index, title, body}, ...]
         ▼
┌─────────────────┐
│  4. Caption     │  LLM generates caption, hashtags, and CTA
│     Writer      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. Quality     │  LLM self-evaluates hook strength, clarity,
│     Scorer      │  and CTA effectiveness (scores 1–10)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  6. Renderer    │  Pillow draws 1080×1350 px PNG per slide
│  (Pillow)       │  Saved to backend/output/{project_id}/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  7. Storage     │  Project metadata saved as JSON in backend/projects/
└─────────────────┘
```

**File layout**

```
backend/
├── main.py                   # FastAPI app, route handlers, quality scorer
├── pipeline/
│   ├── transcript.py         # YouTube transcript retrieval
│   ├── planner.py            # Carousel structure planning
│   ├── slide_writer.py       # Slide copy generation + retry loop
│   ├── caption_writer.py     # Caption + hashtag generation
│   ├── renderer.py           # Pillow image rendering
│   └── validator.py          # Slide validation rules
├── prompts/
│   ├── planner_prompt.py     # Prompt template for planning
│   ├── slide_prompt.py       # Prompt template for slide copy + retry
│   └── caption_prompt.py     # Prompt template for captions
├── output/                   # Generated slide images (git-ignored)
├── projects/                 # Saved project JSON files (git-ignored)
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Design Decisions

**Sequential pipeline over a single mega-prompt**
Each stage has a single, well-scoped job. This makes individual stages easy to tune, retry, and replace without touching the rest of the pipeline. A single prompt producing everything at once is harder to debug when one part of the output is wrong.

**Validation + retry loop on slide copy**
Every slide is validated against hard constraints (5–20 word body, non-empty title) before being accepted. If a slide fails, the prompt is re-sent with the specific constraint appended. This removes an entire class of silent failures where the LLM produces technically structured but out-of-spec content.

**Prompts separated from pipeline logic**
All LLM prompt templates live in `backend/prompts/`. Changing the tone or tightening a constraint never requires touching pipeline code. This also makes A/B testing prompts straightforward.

**Tone as a first-class parameter**
`educational`, `motivational`, and `promotional` tones are injected at prompt-construction time across every stage (planning, slide copy, caption). A single `tone` value on the request shapes the entire output end-to-end without any post-processing.

**LLM quality self-evaluation**
The quality scorer asks the same model to critique its own output after generation. This surfaces obviously weak hooks or vague CTAs without requiring a second model or human review step, which is practical for a prototype where fast iteration matters more than perfect scoring.

**Browser cookies for YouTube transcript access**
YouTube's bot detection blocks programmatic transcript requests from non-browser clients. Rather than routing through a proxy service, the API accepts a Netscape-format cookies file exported from a logged-in browser session. This keeps the setup self-contained with no third-party dependency.

**Local JSON storage for the prototype**
Each project is a single JSON file in `backend/projects/`. There is no database to set up, migrate, or run locally. The schema maps directly to the API response, so the switch to Firestore later is a drop-in replacement of two helper functions.

---

## Environment Variables

See `backend/.env.example` for the full list. Required for local development:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | Model to use — `gpt-4o` or `gpt-4o-mini` |
| `YOUTUBE_COOKIES_FILE` | Path to a Netscape `cookies.txt` exported from your browser |
| `OUTPUT_DIR` | Directory for rendered slide images (default: `output`) |
