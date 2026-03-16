import json
import logging
import os

from openai import OpenAI

from pipeline.validator import validate_slide
from prompts.slide_prompt import build_slide_prompt, build_batch_slides_prompt, build_retry_prompt

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


def generate_slides_batch(slide_plans: list[dict], tone: str) -> list[dict]:
    """
    Generate copy for all slides in a single API call.

    Falls back to per-slide generation if the batch response is unparseable.
    One retry attempt if any slides fail validation.
    """
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def _call_batch(plans: list[dict]) -> list[dict]:
        messages = build_batch_slides_prompt(plans, tone)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI batch slide call failed: {exc}") from exc

        raw = response.choices[0].message.content
        logger.debug("Batch slides raw response: %s", raw)

        try:
            result = _parse_json_response(raw)
            return result.get("slides", [])
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Batch slide response was not valid JSON: {raw!r}") from exc

    raw_slides = _call_batch(slide_plans)

    # Validate and collect failures
    validated = []
    failures = []
    plan_by_index = {p["index"]: p for p in slide_plans}

    for raw in raw_slides:
        index = raw.get("index")
        is_valid, error = validate_slide(raw)
        if is_valid:
            validated.append({"index": index, "title": raw["title"].strip(), "body": raw["body"].strip()})
        else:
            logger.warning("Batch slide %s failed validation (%s) — will retry", index, error)
            failures.append(plan_by_index.get(index, {"index": index, "role": "slide", "idea": ""}))

    # One retry for any failing slides
    if failures:
        logger.info("Retrying %d failed slide(s) individually", len(failures))
        for plan_item in failures:
            slide = _generate_single_slide(client, model, plan_item, tone)
            validated.append(slide)

    # Fill in any slides missing from the response entirely
    returned_indices = {s["index"] for s in validated}
    for plan_item in slide_plans:
        if plan_item["index"] not in returned_indices:
            logger.warning("Slide %d missing from batch response — generating individually", plan_item["index"])
            validated.append(_generate_single_slide(client, model, plan_item, tone))

    validated.sort(key=lambda s: s["index"])
    return validated


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
