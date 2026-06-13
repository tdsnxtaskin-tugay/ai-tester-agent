"""Browser execution — runs a single test with browser-use and records video.

Wraps the browser-use Agent so the rest of the pipeline gets a simple
`run_test(...) -> BrowserRunResult` call.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from . import config
from .prompts import build_agent_task

logger = logging.getLogger(__name__)


@dataclass
class BrowserRunResult:
    feature: str
    history_text: str
    recording_path: Path | None
    completed: bool
    error: str | None = None


class BrowserRunner:
    def __init__(self, llm) -> None:
        self._llm = llm
        config.ensure_output_dirs()

    async def run_test(self, *, feature: str, instructions: str,
                       grounded_block: str = "") -> BrowserRunResult:
        """Execute one test in a real browser and capture a recording."""
        from browser_use import Agent, BrowserSession

        task = build_agent_task(
            feature=feature,
            instructions=instructions,
            base_url=config.agent.target_base_url,
            grounded_block=grounded_block,
        )

        record_dir = config.RAW_RECORDING_DIR if config.agent.record_video else None
        browser_session = BrowserSession(
            headless=config.agent.headless,
            record_video_dir=str(record_dir) if record_dir else None,
        )

        agent = Agent(
            task=task,
            llm=self._llm,
            browser_session=browser_session,
        )

        try:
            history = await agent.run(max_steps=config.agent.max_steps)
            history_text = _summarize_history(history)
            recording = _latest_recording(record_dir) if record_dir else None
            return BrowserRunResult(
                feature=feature,
                history_text=history_text,
                recording_path=recording,
                completed=True,
            )
        except Exception as exc:  # pragma: no cover - depends on live browser
            logger.exception("Browser run failed for '%s'.", feature)
            return BrowserRunResult(
                feature=feature,
                history_text="",
                recording_path=_latest_recording(record_dir) if record_dir else None,
                completed=False,
                error=str(exc),
            )
        finally:
            try:
                await browser_session.close()
            except Exception:
                pass


def _summarize_history(history) -> str:
    """Best-effort extraction of a readable action log from browser-use history."""
    for attr in ("model_actions", "action_results"):
        getter = getattr(history, attr, None)
        if callable(getter):
            try:
                items = getter()
                return "\n".join(str(i) for i in items)
            except Exception:
                continue
    return str(history)


def _latest_recording(record_dir: Path | None) -> Path | None:
    if not record_dir or not record_dir.exists():
        return None
    candidates = sorted(
        [p for p in record_dir.iterdir() if p.suffix in {".webm", ".mkv", ".mp4"}],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None
