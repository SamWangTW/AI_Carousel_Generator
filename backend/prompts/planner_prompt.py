TONE_INSTRUCTIONS = {
    "educational": "Use clear, simple language. Teach one concept per slide.",
    "motivational": "Use bold, energetic language. Start with a strong verb.",
    "promotional": "Focus on benefits. Use persuasive, action-oriented language.",
}

DEFAULT_SLIDE_ROLES = [
    "hook",
    "problem",
    "key insight",
    "supporting idea",
    "example",
    "call to action",
]


def build_planner_prompt(transcript: str, slide_count: int, tone: str) -> list[dict]:
    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["educational"])

    roles = DEFAULT_SLIDE_ROLES[:slide_count]
    if len(roles) < slide_count:
        roles += ["supporting idea"] * (slide_count - len(roles))
    roles_list = "\n".join(f"  Slide {i+1} – {role}" for i, role in enumerate(roles))

    system_message = (
        "You are an expert social media content strategist. "
        "Your job is to analyze video transcripts and plan engaging Instagram carousel posts. "
        "Always respond with valid JSON only — no markdown, no explanation."
    )

    user_message = f"""Analyze the following YouTube video transcript and plan a {slide_count}-slide Instagram carousel post.

TONE: {tone}
TONE INSTRUCTION: {tone_instruction}

SLIDE STRUCTURE TO FOLLOW:
{roles_list}

For each slide, extract the most relevant idea from the transcript that fits that slide's role.

Return a JSON object with this exact structure:
{{
  "main_topic": "the main topic of the video in one sentence",
  "slides": [
    {{
      "index": 1,
      "role": "hook",
      "idea": "the key idea or angle for this slide, drawn from the transcript"
    }}
  ]
}}

TRANSCRIPT:
{transcript}"""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
