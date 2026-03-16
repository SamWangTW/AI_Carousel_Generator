import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, HttpUrl

load_dotenv()

from pipeline.caption_writer import generate_caption
from pipeline.planner import detect_tone, plan_carousel
from pipeline.renderer import render_slides
from pipeline.slide_writer import generate_slides
from pipeline.transcript import fetch_transcript
from pipeline.validator import validate_slide

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Carousel Generator", version="1.0.0")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
PROJECTS_DIR = BASE_DIR / "projects"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ── Request / Response Models ──────────────────────────────────────────────────

class GenerateCarouselRequest(BaseModel):
    video_url: str
    slide_count: int = 6
    tone: str = "auto"


class RegenerateSlideRequest(BaseModel):
    project_id: str
    slide_index: int
    tone: str = "educational"


class RegenerateCaptionRequest(BaseModel):
    project_id: str
    tone: str = "educational"


class UpdateProjectRequest(BaseModel):
    slides: list[dict] | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    cta: str | None = None


# ── Local storage helpers ──────────────────────────────────────────────────────

def _save_project(project: dict) -> None:
    path = PROJECTS_DIR / f"{project['project_id']}.json"
    path.write_text(json.dumps(project, indent=2), encoding="utf-8")


def _load_project(project_id: str) -> dict:
    path = PROJECTS_DIR / f"{project_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return json.loads(path.read_text(encoding="utf-8"))


# ── Quality scoring ────────────────────────────────────────────────────────────

def _score_quality(slides: list[dict], caption: str, tone: str) -> dict:
    """Ask the LLM to self-evaluate the carousel quality."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o")

    slide_summary = "\n".join(
        f"  Slide {s['index']}: {s['title']} — {s['body']}" for s in slides
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a social media content quality evaluator. "
                "Score carousel posts honestly and return only valid JSON."
            ),
        },
        {
            "role": "user",
            "content": f"""Evaluate the quality of this Instagram carousel post.

SLIDES:
{slide_summary}

CAPTION: {caption}
TONE: {tone}

Score each dimension from 1 to 10:
- hook_strength: How compelling is the first slide at stopping the scroll?
- content_clarity: How clear and easy to understand is the overall content?
- cta_effectiveness: How strong and actionable is the call to action?

Return a JSON object:
{{
  "hook_strength": <1-10>,
  "content_clarity": <1-10>,
  "cta_effectiveness": <1-10>,
  "overall": <average of the three, rounded to 1 decimal>
}}""",
        },
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        scores = json.loads(raw)
        # Ensure overall is present
        if "overall" not in scores:
            vals = [scores.get("hook_strength", 5), scores.get("content_clarity", 5), scores.get("cta_effectiveness", 5)]
            scores["overall"] = round(sum(vals) / len(vals), 1)
        return scores
    except Exception as exc:
        logger.warning("Quality scoring failed: %s", exc)
        return {"hook_strength": None, "content_clarity": None, "cta_effectiveness": None, "overall": None}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.post("/generate-carousel")
async def generate_carousel(req: GenerateCarouselRequest):
    """
    Full pipeline: YouTube URL → carousel slides + caption + quality score.
    Slides are rendered as PNG images and saved to backend/output/.
    """
    if req.slide_count < 2 or req.slide_count > 12:
        raise HTTPException(status_code=400, detail="slide_count must be between 2 and 12.")
    if req.tone not in ("auto", "educational", "motivational", "promotional"):
        raise HTTPException(status_code=400, detail="tone must be auto, educational, motivational, or promotional.")

    project_id = str(uuid.uuid4())
    project_output_dir = str(OUTPUT_DIR / project_id)

    # 1. Transcript
    logger.info("[%s] Fetching transcript for %s", project_id, req.video_url)
    try:
        transcript = fetch_transcript(req.video_url)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # 2. Tone detection (when tone is "auto")
    tone_reason = None
    if req.tone == "auto":
        logger.info("[%s] Detecting tone from transcript", project_id)
        try:
            tone_result = detect_tone(transcript)
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        tone = tone_result["tone"]
        tone_reason = tone_result["reason"]
        logger.info("[%s] Detected tone: %s — %s", project_id, tone, tone_reason)
    else:
        tone = req.tone

    # 3. Planning
    logger.info("[%s] Planning carousel structure", project_id)
    try:
        plan = plan_carousel(transcript, req.slide_count, tone)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    slide_plans = plan["slides"]

    # 4. Slide copy generation (includes validation + retry)
    logger.info("[%s] Generating slide copy", project_id)
    try:
        slides = generate_slides(slide_plans, tone)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # 5. Caption generation
    logger.info("[%s] Generating caption", project_id)
    try:
        caption_data = generate_caption(slides, tone)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # 6. Quality scoring
    logger.info("[%s] Scoring quality", project_id)
    quality_score = _score_quality(slides, caption_data["caption"], tone)

    # 7. Render slides
    logger.info("[%s] Rendering slide images", project_id)
    image_paths = render_slides(slides, project_output_dir)
    relative_image_urls = [f"/output/{project_id}/slide_{s['index']}.png" for s in slides]

    # 8. Save project
    project = {
        "project_id": project_id,
        "video_url": req.video_url,
        "tone": tone,
        "tone_reason": tone_reason,
        "slide_count": req.slide_count,
        "main_topic": plan.get("main_topic", ""),
        "transcript": transcript,
        "slides": slides,
        "caption": caption_data["caption"],
        "hashtags": caption_data["hashtags"],
        "cta": caption_data["cta"],
        "quality_score": quality_score,
        "slide_image_paths": image_paths,
        "slide_image_urls": relative_image_urls,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_project(project)
    logger.info("[%s] Project saved", project_id)

    return {
        "project_id": project_id,
        "main_topic": project["main_topic"],
        "tone": tone,
        "tone_reason": tone_reason,
        "slides": slides,
        "caption": caption_data["caption"],
        "hashtags": caption_data["hashtags"],
        "cta": caption_data["cta"],
        "quality_score": quality_score,
        "slide_image_urls": relative_image_urls,
    }


@app.post("/regenerate-slide")
async def regenerate_slide(req: RegenerateSlideRequest):
    """Regenerate a single slide by index and re-render its image."""
    project = _load_project(req.project_id)

    # Find the original plan idea for this slide index
    matching_slides = [s for s in project["slides"] if s["index"] == req.slide_index]
    if not matching_slides:
        raise HTTPException(status_code=404, detail=f"Slide index {req.slide_index} not found in project.")

    existing_slide = matching_slides[0]
    # Reconstruct a minimal plan item
    plan_item = {
        "index": req.slide_index,
        "role": existing_slide.get("role", "slide"),
        "idea": existing_slide.get("body", ""),
    }

    try:
        new_slides = generate_slides([plan_item], req.tone)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    new_slide = new_slides[0]

    # Update project slides in-place
    for i, s in enumerate(project["slides"]):
        if s["index"] == req.slide_index:
            project["slides"][i] = new_slide
            break

    # Re-render just this one slide
    project_output_dir = str(OUTPUT_DIR / req.project_id)
    render_slides([new_slide], project_output_dir)

    _save_project(project)

    return {
        "project_id": req.project_id,
        "slide": new_slide,
        "slide_image_url": f"/output/{req.project_id}/slide_{req.slide_index}.png",
    }


@app.post("/regenerate-caption")
async def regenerate_caption(req: RegenerateCaptionRequest):
    """Regenerate caption, hashtags, and CTA for an existing project."""
    project = _load_project(req.project_id)

    try:
        caption_data = generate_caption(project["slides"], req.tone)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    project["caption"] = caption_data["caption"]
    project["hashtags"] = caption_data["hashtags"]
    project["cta"] = caption_data["cta"]
    _save_project(project)

    return {
        "project_id": req.project_id,
        "caption": caption_data["caption"],
        "hashtags": caption_data["hashtags"],
        "cta": caption_data["cta"],
    }


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Retrieve a saved project by ID."""
    project = _load_project(project_id)
    # Don't expose the full transcript in the response
    project.pop("transcript", None)
    return project


@app.patch("/projects/{project_id}")
async def update_project(project_id: str, req: UpdateProjectRequest):
    """Apply user edits (slide text, caption, hashtags, CTA) to a saved project."""
    project = _load_project(project_id)

    if req.slides is not None:
        # Validate any edited slides before saving
        for slide in req.slides:
            is_valid, error = validate_slide(slide)
            if not is_valid:
                raise HTTPException(
                    status_code=422,
                    detail=f"Slide {slide.get('index')} failed validation: {error}",
                )
        project["slides"] = req.slides

    if req.caption is not None:
        project["caption"] = req.caption
    if req.hashtags is not None:
        project["hashtags"] = req.hashtags
    if req.cta is not None:
        project["cta"] = req.cta

    _save_project(project)
    return {"project_id": project_id, "status": "updated"}


@app.post("/export-carousel")
async def export_carousel(body: dict):
    """Return the list of slide image URLs for a project (ready for download)."""
    project_id = body.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required.")

    project = _load_project(project_id)
    return {
        "project_id": project_id,
        "slide_image_urls": project.get("slide_image_urls", []),
    }
