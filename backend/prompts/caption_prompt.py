from prompts.planner_prompt import TONE_INSTRUCTIONS


def build_caption_prompt(slides: list[dict], tone: str) -> list[dict]:
    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["educational"])

    slide_summary = "\n".join(
        f"  Slide {s['index']}: {s['title']} — {s['body']}" for s in slides
    )

    system_message = (
        "You are a social media strategist who writes high-performing Instagram captions. "
        "Your captions drive engagement, use strategic hashtags, and always include a clear CTA. "
        "Always respond with valid JSON only — no markdown, no explanation."
    )

    user_message = f"""Write an Instagram caption for a carousel post with the following slides:

{slide_summary}

TONE: {tone}
TONE INSTRUCTION: {tone_instruction}

REQUIREMENTS:
- caption: 1–3 engaging sentences that hook the reader and summarise the carousel value
- hashtags: 7–10 relevant hashtags as a JSON array of strings (include the # symbol)
- cta: one punchy call-to-action line (e.g. "Save this for later", "Share with someone who needs this")

Return a JSON object with this exact structure:
{{
  "caption": "your caption text here",
  "hashtags": ["#tag1", "#tag2", "#tag3"],
  "cta": "your call-to-action here"
}}"""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
