"""Result matching — uses GPT to decide PASS/FAIL from the agent's actions.

Compares the intended test steps against what the browser agent actually did
and returns a strict verdict. Falls back to a heuristic if the model output
cannot be parsed.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from .config import azure_openai
from .prompts import RESULT_MATCH_SYSTEM, build_result_match_prompt

logger = logging.getLogger(__name__)


@dataclass
class Verdict:
    outcome: str  # "Passed" | "Failed"
    reason: str
    failed_step: int | None = None


class ResultMatcher:
    def __init__(self, chat_client) -> None:
        self._client = chat_client

    def evaluate(self, *, feature: str, instructions: str,
                 agent_history: str, run_completed: bool) -> Verdict:
        if not run_completed:
            return Verdict("Failed", "Browser run did not complete.", None)
        if not agent_history.strip():
            return Verdict("Failed", "No agent actions were recorded.", None)

        prompt = build_result_match_prompt(feature, instructions, agent_history)
        try:
            resp = self._client.chat.completions.create(
                model=azure_openai.deployment,
                messages=[
                    {"role": "system", "content": RESULT_MATCH_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            return self._parse(resp.choices[0].message.content)
        except Exception as exc:
            logger.error("Result matching call failed: %s", exc)
            return Verdict("Failed", f"Result matching error: {exc}", None)

    @staticmethod
    def _parse(content: str | None) -> Verdict:
        if not content:
            return Verdict("Failed", "Empty model response.", None)
        try:
            data = json.loads(content)
            outcome = str(data.get("outcome", "Failed")).capitalize()
            if outcome not in {"Passed", "Failed"}:
                outcome = "Failed"
            step = data.get("failed_step")
            return Verdict(
                outcome=outcome,
                reason=str(data.get("reason", "")).strip() or "No reason provided.",
                failed_step=int(step) if isinstance(step, int) else None,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Could not parse verdict JSON: %s", exc)
            return Verdict("Failed", "Unparseable model verdict.", None)
