import http.cookiejar
import os
import re

import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled


def _extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from a URL or return it directly if already an ID."""
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    # Assume the input is already a bare video ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
        return url.strip()
    raise ValueError(f"Could not extract a YouTube video ID from: {url!r}")


def _clean_transcript(raw_segments) -> str:
    """Join transcript segments into a single clean string."""
    texts = [seg.text.strip() for seg in raw_segments]
    joined = " ".join(texts)
    # Collapse multiple spaces and normalise whitespace
    joined = re.sub(r"\s+", " ", joined).strip()
    # Remove common auto-caption artefacts like [Music] or [Applause]
    joined = re.sub(r"\[.*?\]", "", joined)
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined


def _build_api() -> YouTubeTranscriptApi:
    """Build a YouTubeTranscriptApi instance, optionally loading browser cookies."""
    cookies_path = os.getenv("YOUTUBE_COOKIES_FILE")
    if cookies_path and os.path.exists(cookies_path):
        session = requests.Session()
        jar = http.cookiejar.MozillaCookieJar(cookies_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies = jar
        return YouTubeTranscriptApi(http_client=session)
    return YouTubeTranscriptApi()


def fetch_transcript(video_url: str) -> str:
    """
    Fetch and clean the transcript for a YouTube video.

    Args:
        video_url: Full YouTube URL or bare video ID.

    Returns:
        A clean, single-string transcript ready for LLM input.

    Raises:
        ValueError: If the video ID cannot be extracted.
        RuntimeError: If no transcript is available for the video.
    """
    video_id = _extract_video_id(video_url)
    api = _build_api()

    try:
        transcript = api.fetch(video_id)
    except TranscriptsDisabled:
        raise RuntimeError(
            f"Transcripts are disabled for video '{video_id}'. "
            "This video does not have captions available."
        )
    except NoTranscriptFound:
        raise RuntimeError(
            f"No transcript found for video '{video_id}'. "
            "Try a video that has auto-generated or manual captions."
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch transcript for '{video_id}': {exc}") from exc

    if not transcript:
        raise RuntimeError(f"Transcript for '{video_id}' is empty.")

    return _clean_transcript(transcript)
