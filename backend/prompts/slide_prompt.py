from prompts.planner_prompt import TONE_INSTRUCTIONS


def build_slide_prompt(slide_plan_item: dict, tone: str) -> list[dict]:
    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["educational"])
    role = slide_plan_item.get("role", "slide")
    idea = slide_plan_item.get("idea", "")
    index = slide_plan_item.get("index", 1)

    system_message = (
        "You are a concise social media copywriter specialising in Instagram carousel posts. "
        "Write punchy, scroll-stopping slide copy. "
        "Always respond with valid JSON only — no markdown, no explanation."
    )

    user_message = f"""Write the copy for slide {index} of an Instagram carousel post.

SLIDE ROLE: {role}
KEY IDEA: {idea}
TONE: {tone}
TONE INSTRUCTION: {tone_instruction}

STRICT REQUIREMENTS:
- title: short, attention-grabbing (max 8 words)
- body: between 5 and 20 words — this is a hard limit
- No emojis unless the tone calls for it
- Write for mobile — short sentences, punchy language

Return a JSON object with this exact structure:
{{
  "title": "slide title here",
  "body": "slide body text here, strictly between 5 and 20 words"
}}"""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def build_batch_slides_prompt(slide_plans: list[dict], tone: str) -> list[dict]:
    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["educational"])

    slides_list = "\n".join(
        f'  Slide {p["index"]} ({p["role"]}): {p["idea"]}'
        for p in slide_plans
    )

    system_message = (
        "You are a concise social media copywriter specialising in Instagram carousel posts. "
        "Write punchy, scroll-stopping slide copy. "
        "Always respond with valid JSON only — no markdown, no explanation."
    )

    user_message = f"""Write copy for ALL slides of an Instagram carousel post in one response.

TONE: {tone}
TONE INSTRUCTION: {tone_instruction}

SLIDES TO WRITE:
{slides_list}

STRICT REQUIREMENTS FOR EVERY SLIDE:
- title: short, attention-grabbing (max 8 words)
- body: between 5 and 20 words — this is a hard limit, count carefully
- No emojis unless the tone calls for it
- Write for mobile — short sentences, punchy language

Return a JSON object with this exact structure:
{{
  "slides": [
    {{"index": 1, "title": "title here", "body": "body text here, strictly between 5 and 20 words"}},
    {{"index": 2, "title": "title here", "body": "body text here, strictly between 5 and 20 words"}}
  ]
}}

Include all {len(slide_plans)} slides in the array."""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def build_retry_prompt(messages: list[dict], error_message: str) -> list[dict]:
    """Append a stricter constraint reminder to an existing message list for retry."""
    updated = list(messages)
    updated.append({
        "role": "assistant",
        "content": "[previous attempt failed validation]",
    })
    updated.append({
        "role": "user",
        "content": (
            f"Your previous response failed validation: {error_message}\n\n"
            "Please try again. IMPORTANT REMINDERS:\n"
            "- Body text MUST be between 5 and 20 words — count carefully\n"
            "- Title MUST be non-empty\n"
            "- Return valid JSON only: {\"title\": \"...\", \"body\": \"...\"}"
        ),
    })
    return updated
