import json
import logging
import os

from openai import OpenAI

from prompts.planner_prompt import build_planner_prompt

logger = logging.getLogger(__name__)


def _get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _parse_json_response(content: str) -> dict:
    """Strip markdown fences if present and parse JSON."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


def plan_carousel(transcript: str, slide_count: int, tone: str) -> dict:
    """
    Use the LLM to analyse the transcript and produce a structured carousel plan.

    Args:
        transcript: Cleaned transcript text from transcript.py.
        slide_count: Desired number of slides.
        tone: One of "educational", "motivational", "promotional".

    Returns:
        Dict with keys:
            "main_topic": str
            "slides": list of {"index": int, "role": str, "idea": str}

    Raises:
        RuntimeError: On API failure or unparseable response.
    """
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    messages = build_planner_prompt(transcript, slide_count, tone)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed during planning: {exc}") from exc

    raw = response.choices[0].message.content
    logger.debug("Planner raw response: %s", raw)

    try:
        result = _parse_json_response(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Planner returned invalid JSON: {raw!r}") from exc

    if "slides" not in result or not isinstance(result["slides"], list):
        raise RuntimeError(f"Planner response missing 'slides' key: {result}")

    # Ensure the number of slides matches the request
    slides = result["slides"][:slide_count]
    if len(slides) < slide_count:
        logger.warning(
            "Planner returned %d slides but %d were requested.", len(slides), slide_count
        )

    result["slides"] = slides
    return result
