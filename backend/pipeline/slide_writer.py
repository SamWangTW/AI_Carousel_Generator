import json
import logging
import os

from openai import OpenAI

from pipeline.validator import validate_slide
from prompts.slide_prompt import build_slide_prompt, build_retry_prompt

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


def _get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _parse_json_response(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


def _generate_single_slide(
    client: OpenAI,
    model: str,
    slide_plan_item: dict,
    tone: str,
) -> dict:
    """
    Generate copy for one slide with validation and auto-retry.

    Returns a validated slide dict: {"index": int, "title": str, "body": str}
    Falls back to a best-effort result if all retries fail.
    """
    messages = build_slide_prompt(slide_plan_item, tone)
    last_error = ""

    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            logger.warning(
                "Slide %d retry %d/%d — previous error: %s",
                slide_plan_item.get("index"),
                attempt,
                MAX_RETRIES,
                last_error,
            )
            messages = build_retry_prompt(messages, last_error)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise RuntimeError(
                f"OpenAI API call failed for slide {slide_plan_item.get('index')}: {exc}"
            ) from exc

        raw = response.choices[0].message.content
        logger.debug("Slide %d raw response: %s", slide_plan_item.get("index"), raw)

        try:
            slide = _parse_json_response(raw)
        except json.JSONDecodeError:
            last_error = f"Response was not valid JSON: {raw!r}"
            continue

        is_valid, error_message = validate_slide(slide)
        if is_valid:
            return {
                "index": slide_plan_item["index"],
                "title": slide["title"].strip(),
                "body": slide["body"].strip(),
            }

        last_error = error_message

    # All retries exhausted — return best-effort result with a warning
    logger.error(
        "Slide %d failed validation after %d retries. Using last result.",
        slide_plan_item.get("index"),
        MAX_RETRIES,
    )
    try:
        slide = _parse_json_response(
            client.chat.completions.create(
                model=model,
                messages=build_slide_prompt(slide_plan_item, tone),
                response_format={"type": "json_object"},
            ).choices[0].message.content
        )
        return {
            "index": slide_plan_item["index"],
            "title": slide.get("title", "").strip(),
            "body": slide.get("body", "").strip(),
        }
    except Exception:
        return {
            "index": slide_plan_item["index"],
            "title": slide_plan_item.get("role", "Slide").title(),
            "body": slide_plan_item.get("idea", "Content coming soon."),
        }


def generate_slides(slide_plans: list[dict], tone: str) -> list[dict]:
    """
    Generate validated copy for all slides in the carousel plan.

    Args:
        slide_plans: List of slide plan dicts from planner.py
                     (each has "index", "role", "idea").
        tone: One of "educational", "motivational", "promotional".

    Returns:
        List of slide dicts: [{"index": int, "title": str, "body": str}, ...]
        Ordered by index ascending.
    """
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    slides = []

    for plan_item in slide_plans:
        slide = _generate_single_slide(client, model, plan_item, tone)
        slides.append(slide)

    slides.sort(key=lambda s: s["index"])
    return slides
