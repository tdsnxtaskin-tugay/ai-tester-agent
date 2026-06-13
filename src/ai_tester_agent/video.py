"""Video post-processing — convert raw browser recordings to shareable .mp4.

browser-use records sessions as .webm/.mkv. Azure DevOps test runs and demo
videos are easier to consume as .mp4, so we transcode with FFmpeg if available.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def to_mp4(source: Path, dest_dir: Path) -> Path | None:
    """Transcode a raw recording to .mp4.

    Returns the .mp4 path, or the original file if FFmpeg is unavailable, or
    None if the source does not exist.
    """
    if not source.exists():
        logger.warning("Recording not found: %s", source)
        return None

    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / (source.stem + ".mp4")

    if not ffmpeg_available():
        logger.warning(
            "FFmpeg not on PATH — skipping transcode; using raw recording %s.",
            source.name,
        )
        return source

    cmd = [
        "ffmpeg", "-y", "-i", str(source),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", str(target),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info("Transcoded recording -> %s", target.name)
        return target
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.error("FFmpeg transcode failed (%s); using raw recording.", exc)
        return source
