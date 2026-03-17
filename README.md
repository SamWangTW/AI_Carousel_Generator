# AI Carousel Generator

Converts a YouTube video into a ready-to-post Instagram carousel. Paste a URL, choose a tone, and get back slide images, a caption, hashtags, and a quality score — all in one API call.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | Python 3.10 · FastAPI · Uvicorn |
| AI | OpenAI API (`gpt-5-mini`) |
| Transcript | `youtube-transcript-api` 1.2.4 |
| Image Rendering | Pillow — 1080 × 1350 px PNG (Instagram portrait) |
| Storage | Local JSON (prototype) |
| Containerisation | Docker |
| Mobile | React Native · Expo Go |

---

## How to Run Locally

**Prerequisites:** Python 3.10+, Node.js, an OpenAI API key with billing enabled, and the Expo Go app on your phone.

### Run everything (backend + mobile) with one command

```bash
# From the project root
npm install
npm run dev
```

This starts the FastAPI backend on port 8000 and the Expo bundler together. Backend logs appear with an `[API]` prefix. Scan the QR code with Expo Go to open the app.

You can also run them separately:

```bash
npm run api     # FastAPI backend only
npm run mobile  # Expo bundler only
```

### Backend only (manual setup)

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Open .env and set OPENAI_API_KEY and OPENAI_MODEL

# 3. (Required) Export YouTube cookies to bypass bot detection
#    Install the "Get cookies.txt LOCALLY" browser extension,
#    visit youtube.com while logged in, export → save as backend/cookies.txt
#    Then set in .env: YOUTUBE_COOKIES_FILE=cookies.txt

# 4. Start the server
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

## Mobile App

The Expo Go app connects to your local backend over Wi-Fi (both devices must be on the same network).

**Screens:**

- **Home** — enter a YouTube URL, choose slide count (2–12), tap Generate. Tone is detected automatically.
- **Results** — horizontal carousel preview of all slides, share the active slide via the native share sheet, copy caption and hashtags to clipboard.

**Share flow:** The "Share Slide X of Y" button downloads the currently visible slide to the device cache and opens the native share sheet (Instagram, WhatsApp, Save to Photos, etc.). Swipe to the next slide and tap again to share it.

> Expo Go does not support saving directly to the camera roll on Android due to OS-level permission restrictions. Use a development build for that feature.

---

## API Reference

### `POST /generate-carousel`

Full pipeline: YouTube URL → slide images + caption + quality score.

**Request**

```json
{
  "video_url": "https://www.youtube.com/watch?v=iJYhGD96NxA",
  "slide_count": 6,
  "tone": "auto",
  "score_quality": false
}
```

| Field | Type | Default | Options |
|---|---|---|---|
| `video_url` | string | — | Any YouTube URL or bare video ID |
| `slide_count` | int | `6` | `2` – `12` |
| `tone` | string | `"auto"` | `auto` · `educational` · `motivational` · `promotional` |
| `score_quality` | bool | `false` | `true` to enable LLM quality scoring |

> When `tone` is `"auto"` (the default), the pipeline analyses the transcript and picks the best tone automatically. The detected tone and its reason are returned in the response.

**Response**

```json
{
  "project_id": "1b43c1e7-873c-4aed-907b-e523d685a9b4",
  "main_topic": "How to get your first online coaching clients",
  "tone": "educational",
  "tone_reason": "The video teaches a step-by-step outreach process with specific tactics and examples.",
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
  "quality_score": null,
  "slide_image_urls": [
    "/output/1b43c1e7-.../slide_1.png",
    "/output/1b43c1e7-.../slide_2.png"
  ]
}
```

> `quality_score` is `null` unless `score_quality: true` is passed in the request.
> `hashtags` always contains exactly 5 tags.

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
┌──────────────────────────────────────────────┐  ← parallel
│  2a. Tone Detection    │  2b. Planner         │
│  (tone="auto" only)    │  Structures carousel │
│  LLM picks best tone   │  Hook → Problem →    │
│  returns {tone,reason} │  Insight → CTA       │
└────────────────────────┴──────────┬───────────┘
                                    │ slide plan [{index, role, idea}, ...]
                                    ▼
┌──────────────────────────────────────────────┐  ← parallel
│  3a. Slide Writer          │  3b. Caption     │
│  + Validator/Retry         │      Writer      │
│  Batch LLM call for all    │  LLM generates   │
│  slides; validates each;   │  caption (5       │
│  retries failures          │  hashtags), CTA  │
└────────────────────────────┴──────────┬───────┘
                                        │
                                        ▼
                             ┌─────────────────┐
                             │  4. Quality     │  (optional, score_quality=true)
                             │     Scorer      │  LLM self-evaluates hook,
                             └────────┬────────┘  clarity, CTA (scores 1–10)
                                      │
                                      ▼
                             ┌─────────────────┐
                             │  5. Renderer    │  Pillow draws 1080×1350 px PNG
                             │  (Pillow)       │  backend/output/{project_id}/
                             └────────┬────────┘
                                      │
                                      ▼
                             ┌─────────────────┐
                             │  6. Storage     │  Project JSON → backend/projects/
                             └─────────────────┘
```

**File layout**

```
AI_Carousel_Generator/
├── backend/
│   ├── main.py                   # FastAPI app, route handlers, quality scorer
│   ├── pipeline/
│   │   ├── transcript.py         # YouTube transcript retrieval
│   │   ├── planner.py            # Carousel structure planning
│   │   ├── slide_writer.py       # Slide copy generation + retry loop
│   │   ├── caption_writer.py     # Caption + hashtag generation
│   │   ├── renderer.py           # Pillow image rendering
│   │   └── validator.py          # Slide validation rules
│   ├── prompts/
│   │   ├── planner_prompt.py     # Prompt template for planning
│   │   ├── slide_prompt.py       # Prompt template for slide copy + retry
│   │   └── caption_prompt.py     # Prompt template for captions
│   ├── output/                   # Generated slide images (git-ignored)
│   ├── projects/                 # Saved project JSON files (git-ignored)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── mobile/
│   ├── src/
│   │   ├── screens/
│   │   │   ├── HomeScreen.js     # URL input, slide count, generate button
│   │   │   └── ResultsScreen.tsx # Carousel preview, share, copy caption/hashtags
│   │   ├── components/
│   │   │   └── SlideCounter.js   # ± slide count picker
│   │   └── api/
│   │       └── carousel.js       # generateCarousel() API client
│   ├── App.js                    # Navigation stack
│   └── app.json                  # Expo config
├── scripts/
│   └── dev.js                    # Starts backend + Expo together
└── package.json                  # Root scripts: dev, api, mobile
```

---

## Design Decisions

**Staged pipeline over a single mega-prompt**
Each stage has a single, well-scoped job. This makes individual stages easy to tune, retry, and replace without touching the rest of the pipeline. A single prompt producing everything at once is harder to debug when one part of the output is wrong.

**Parallel execution where possible**
Tone detection and planning run concurrently (both only need the transcript). Slide writing and caption generation also run concurrently (both only need the plan). This cuts the wall-clock time of the two most expensive LLM steps roughly in half.

**Per-stage timing logs**
Every pipeline stage logs its elapsed time to the terminal as it completes, followed by a one-line summary of the full run. This makes it easy to spot which stage is the bottleneck without adding any external tooling.

**Validation + retry loop on slide copy**
Every slide is validated against hard constraints (5–20 word body, non-empty title) before being accepted. If a slide fails, the prompt is re-sent with the specific constraint appended. This removes an entire class of silent failures where the LLM produces technically structured but out-of-spec content.

**Batch slide generation with per-slide fallback**
All slides are requested in a single API call to reduce latency and token overhead. If any slides fail validation, only those are retried individually — the rest are kept, avoiding a full regeneration.

**Prompts separated from pipeline logic**
All LLM prompt templates live in `backend/prompts/`. Changing the tone or tightening a constraint never requires touching pipeline code. This also makes A/B testing prompts straightforward.

**Tone as a first-class parameter**
`educational`, `motivational`, and `promotional` tones are injected at prompt-construction time across every stage (slide copy, caption). A single `tone` value on the request shapes the entire output end-to-end without any post-processing. The planner is intentionally tone-agnostic so it can run in parallel with tone detection.

**Optional LLM quality self-evaluation**
The quality scorer asks the same model to critique its own output after generation. It is opt-in (`score_quality=true`) to keep the default response fast. This surfaces obviously weak hooks or vague CTAs without requiring a second model or human review step.

**Fixed hashtag count**
The caption prompt enforces exactly 5 hashtags. Instagram's algorithm treats hashtag-stuffed posts as spam; a tight, relevant set of 5 outperforms a broad set of 20.

**Share-per-slide on mobile**
`expo-sharing` only supports one file at a time, and Expo Go cannot access the camera roll directly on Android. The mobile app shares whichever slide is currently visible in the carousel, keeping the flow fast (one download, one share sheet) and compatible with Expo Go without requiring a development build.

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
| `OPENAI_MODEL` | Model to use — `gpt-5-mini` |
| `YOUTUBE_COOKIES_FILE` | Path to a Netscape `cookies.txt` exported from your browser |
| `OUTPUT_DIR` | Directory for rendered slide images (default: `output`) |
