# AI Carousel Generator – System Design

## Overview

This project is a prototype that converts a YouTube video into an Instagram-style carousel post using AI.
The system analyzes a video transcript, extracts key ideas, generates slide content, renders carousel images, and allows the user to review and export the result.

The goal is to demonstrate an AI-powered content repurposing pipeline aligned with the skills required by the Taja AI Engineer role:
- Python backend
- AI pipeline with validation and retry logic
- Google Cloud deployment readiness
- Mobile-first workflow (React Native)

---

## Prototype Scope (Interview Demo)

### Goal
Demonstrate a clean, well-engineered AI pipeline that can be run locally in 5 minutes.
Focus is on AI pipeline quality, prompt engineering, and Cloud-ready architecture.

### What's Included in the Prototype
- FastAPI backend
- Single working endpoint: `POST /generate-carousel`
- YouTube transcript retrieval via `youtube-transcript-api`
- AI pipeline: transcript → planning → slide copy → caption + hashtags
- Output validation layer with auto-retry on failure
- Tone-aware prompt system
- Quality scoring via LLM self-evaluation
- Slide image rendering with Pillow (saved locally)
- Dockerfile for Cloud Run readiness
- `.env.example` for easy setup
- Clear README with setup and run instructions

### What's Excluded from the Prototype
- Google Cloud deployment (code is Cloud Run ready via Dockerfile)
- Firestore database (use local JSON for now)
- Authentication
- Instagram publishing (export assets only)

### Folder Structure
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
│   ├── Dockerfile                # Cloud Run ready container
│   ├── requirements.txt
│   └── .env.example
├── system_design.md
└── README.md
```

---

## Product Goal

Enable users to:
1. Paste a YouTube video URL
2. Automatically generate a carousel post
3. Edit slide text and caption
4. Save or export the carousel
5. Optionally publish to Instagram (future)

Example output:
- 6 carousel slides
- Caption
- Hashtags
- Exported images ready for posting

---

## Tech Stack

### Frontend
**React Native (Expo)**

Reasons:
- CEO confirmed mobile-first product focus
- Fast development cycle
- Easy preview of carousel slides on device

Main screens:
- Generate Carousel
- Carousel Preview / Edit
- My Projects
- Login (optional)

### Backend
**Python + FastAPI**

Reasons:
- Excellent ecosystem for AI workflows
- Lightweight and fast API framework
- Easy integration with OpenAI APIs

Responsibilities:
- Handle user requests
- Manage AI generation pipeline
- Validate and retry AI outputs
- Generate carousel images
- Store project data
- Manage job status

### AI Layer
**OpenAI API**

Used for:
- Transcript understanding
- Topic extraction
- Carousel outline generation
- Slide text generation
- Caption generation
- Hashtag generation
- Output quality self-evaluation

Pipeline structure:
1. Transcript analysis
2. Carousel planning
3. Slide copy generation + validation
4. Caption generation
5. Quality scoring

### Transcript Source
Primary approach: **YouTube transcript retrieval**

Library: `youtube-transcript-api`

Benefits:
- Free
- Fast
- Avoids audio processing cost

Fallback (future improvement):
- Whisper transcription for videos without captions

### Slide Rendering
**Python Pillow**

Generate:
- 1080 × 1350 slide images
- Fixed visual templates
- Text overlay
- Optional thumbnail background

Benefits:
- Deterministic output
- Low cost
- Easy to implement

### Cloud Infrastructure
**Google Cloud**

#### Deployment
Cloud Run

Reasons:
- Easy container deployment via Dockerfile
- Scales automatically
- Supports Python services

#### Storage
Google Cloud Storage

Used for:
- Slide images
- Generated assets

#### Database
Firestore

Stores:
- User projects
- Slide metadata
- Captions
- Generation status

---

## High-Level Architecture

```text
React Native App
        |
        v
FastAPI Backend (Cloud Run)
        |
        v
Transcript Retrieval Layer
        |
        v
AI Content Pipeline (OpenAI)
        |
        v
Validation + Retry Layer
        |
        v
Slide Renderer (Pillow)
        |
        v
Cloud Storage (images)
        |
        v
Firestore (project metadata)
```

---

## System Workflow

### 1. User Input
User pastes video URL in mobile app.

Example: `https://youtube.com/video_id`

User taps **Generate Carousel**.

### 2. Backend Request
Mobile app sends:
```
POST /generate-carousel
```

Payload:
```json
{
  "video_url": "...",
  "slide_count": 6,
  "tone": "educational"
}
```

### 3. Transcript Retrieval
Backend fetches transcript using `youtube-transcript-api`.
Transcript is cleaned and formatted for LLM input.

### 4. Carousel Planning
LLM extracts:
- Main topic
- Key insights
- Potential hooks

Then generates carousel structure:
- Slide 1 – Hook
- Slide 2 – Problem
- Slide 3 – Key insight
- Slide 4 – Supporting idea
- Slide 5 – Example
- Slide 6 – CTA

### 5. Slide Copy Generation
LLM generates short text per slide.

Constraints:
- Max 20 words
- Concise statements
- Social-media friendly

### 6. Validation + Auto-Retry
Each slide is validated before proceeding.

Validation rules:
- Must have a title
- Body must be between 5 and 20 words
- No empty fields

If validation fails, pipeline retries with a stricter prompt (max 2 retries).

Example retry logic:
```python
MAX_RETRIES = 2

for attempt in range(MAX_RETRIES):
    slide = generate_slide(prompt)
    if validate_slide(slide):
        break
    else:
        prompt += "\nIMPORTANT: Keep body text strictly under 20 words."
```

### 7. Tone-Aware Prompt System
Prompts adapt based on the tone parameter:

```python
TONE_INSTRUCTIONS = {
    "educational": "Use clear, simple language. Teach one concept per slide.",
    "motivational": "Use bold, energetic language. Start with a strong verb.",
    "promotional": "Focus on benefits. Use persuasive, action-oriented language."
}
```

### 8. Caption Generation
LLM generates:
- Caption
- Hashtags
- Call-to-action

Example:
- Caption: Turning long-form videos into carousel posts can dramatically increase reach.
- Hashtags: #contentcreation #socialmedia #creatorworkflow

### 9. Quality Scoring
LLM self-evaluates the full carousel output:

Scored on:
- Hook strength (1–10)
- Content clarity (1–10)
- CTA effectiveness (1–10)

Returns JSON for optional display to user or internal logging.

### 10. Slide Rendering
Backend renders slide images using Pillow.

Template:
- White background
- Title text
- Body text
- Brand accent color

Generated images saved to `/output/`:
- slide_1.png through slide_6.png

In production: uploaded to Google Cloud Storage.

### 11. Store Project Data
Firestore (production) / local JSON (prototype) stores:
- project_id
- user_id
- video_url
- transcript
- slide_text
- slide_images
- caption
- hashtags
- quality_score
- created_at
- status

### 12. Return Result
Backend returns:
- Slides
- Caption
- Hashtags
- Quality score

Mobile app displays preview. User can:
- Edit slide text
- Regenerate a single slide
- Regenerate caption
- Reorder slides

---

## Agent-Like Pipeline Design

The pipeline is designed to move beyond a simple chain of API calls toward an agent-like system:

- **Validation layer** catches bad outputs before they proceed
- **Auto-retry** adjusts prompts dynamically on failure
- **Tone awareness** adapts generation strategy per user input
- **Self-evaluation** allows the system to assess its own output quality

This enables autonomous operation with minimal user intervention — aligned with the product goal of content repurposing without manual input.

---

## Authentication Strategy

Authentication is optional at generation stage.

Guest users can generate a carousel.

Login required to:
- Save project
- Revisit carousel later
- Publish to Instagram

Suggested login methods:
- Google OAuth
- Magic email link

---

## API Endpoints

```
POST /generate-carousel
POST /regenerate-slide
POST /regenerate-caption
GET  /projects/{id}
PATCH /projects/{id}
POST /export-carousel
POST /publish-instagram
```

---

## Instagram Integration (Future)

After user approves carousel:
1. Connect Instagram professional account
2. Create carousel container
3. Upload images
4. Publish post

For MVP: export assets only.

---

## Scalability Considerations

Future improvements:
- Async job processing with Google Pub/Sub or Cloud Tasks
- Media pipeline workers
- Transcript caching
- Batch AI processing

---

## Design Decisions

### AI-first draft
System generates a draft, not a final post. Users can edit before publishing.

### Fixed slide templates
Deterministic rendering improves consistency, speed, and reliability.

### Transcript-first approach
Avoids heavy video processing in MVP.

### Regenerate individual components
Users can regenerate a single slide, caption, or hashtags instead of the full carousel.

### Validation and retry
Ensures minimum output quality without relying solely on prompt engineering.

### Separated prompt files
All prompt templates live in `/prompts/` for easy tuning and version control — critical for iterative AI development.

---

## Future Improvements

- Full video transcription via Whisper
- Multi-style carousel templates
- Brand kit integration
- Auto-publish scheduling
- Analytics for post performance
- TikTok / LinkedIn / Twitter support

---

## Role of Golang in Production

Although the prototype uses Python, Golang could later support:
- High-throughput media services
- Job orchestration
- Publishing pipelines
- Webhook processing
- Infrastructure services

Python remains the primary language for the AI pipeline.

---

## Summary

This system demonstrates:
- AI-driven content repurposing with validation and retry logic
- Agent-like pipeline design for autonomous operation
- Mobile-first creator workflow
- Scalable, Cloud Run-ready architecture
- Cost-efficient media generation pipeline

The design balances AI capability, product usability, and engineering simplicity — suitable for rapid prototyping and future production scaling.
