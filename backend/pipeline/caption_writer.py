import json
import logging
import os

from openai import OpenAI

from prompts.caption_prompt import build_caption_prompt, build_caption_from_plan_prompt

logger = logging.getLogger(__name__)


def _get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _parse_json_response(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


def generate_caption_from_plan(slide_plans: list[dict], tone: str) -> dict:
    """
    Generate a caption from the carousel plan (role+idea) rather than final slide copy.
    Used to run caption generation in parallel with slide writing.
    """
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    messages = build_caption_from_plan_prompt(slide_plans, tone)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed during caption generation: {exc}") from exc

    raw = response.choices[0].message.content
    logger.debug("Caption (from plan) raw response: %s", raw)

    try:
        result = _parse_json_response(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Caption writer returned invalid JSON: {raw!r}") from exc

    return {
        "caption": result.get("caption", "").strip(),
        "hashtags": result.get("hashtags", []),
        "cta": result.get("cta", "").strip(),
    }


def generate_caption(slides: list[dict], tone: str) -> dict:
    """
    Generate a caption, hashtags, and CTA for the carousel.

    Args:
        slides: Validated slide list from slide_writer.py
                (each has "index", "title", "body").
        tone: One of "educational", "motivational", "promotional".

    Returns:
        Dict with keys:
            "caption": str
            "hashtags": list[str]
            "cta": str

    Raises:
        RuntimeError: On API failure or unparseable response.
    """
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    messages = build_caption_prompt(slides, tone)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed during caption generation: {exc}") from exc

    raw = response.choices[0].message.content
    logger.debug("Caption raw response: %s", raw)

    try:
        result = _parse_json_response(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Caption writer returned invalid JSON: {raw!r}") from exc

    return {
        "caption": result.get("caption", "").strip(),
        "hashtags": result.get("hashtags", []),
        "cta": result.get("cta", "").strip(),
    }
