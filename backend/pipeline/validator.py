def validate_slide(slide: dict) -> tuple[bool, str]:
    """
    Validate a single slide object against the required constraints.

    Args:
        slide: Dict with at minimum {"title": str, "body": str}

    Returns:
        (is_valid, error_message) — error_message is empty string when valid.
    """
    title = slide.get("title", "")
    body = slide.get("body", "")

    if not isinstance(title, str) or not title.strip():
        return False, "Title is missing or empty."

    if not isinstance(body, str) or not body.strip():
        return False, "Body is missing or empty."

    word_count = len(body.strip().split())
    if word_count < 5:
        return False, f"Body is too short ({word_count} words). Minimum is 5 words."

    if word_count > 20:
        return False, f"Body is too long ({word_count} words). Maximum is 20 words."

    return True, ""
