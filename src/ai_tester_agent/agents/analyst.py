"""Analyst agent — assesses delivery quality and decides whether to replan.

Reads the test report, reasons (grounded by the mission's Foundry IQ summary)
about whether failures are real bugs or flawed test steps, and may ask the
Planner to refine the plan once (bounded replan loop).
"""
from __future__ import annotations

import json
import logging

from ..config import azure_openai
from ..prompts import ANALYST_SYSTEM, build_analyst_prompt
from .base import CollaboratingAgent, Mission

logger = logging.getLogger(__name__)

MAX_REPLANS = 1


def results_table(mission: Mission) -> str:
    if not mission.report:
        return "(no results)"
    rows = []
    for o in mission.report.outcomes:
        rows.append(
            f"- [{o.verdict.outcome}] {o.test_case.title}: {o.verdict.reason}"
        )
    return "\n".join(rows)


class AnalystAgent(CollaboratingAgent):
    name = "Analyst"

    def __init__(self, chat_client) -> None:
        self._chat = chat_client

    async def act(self, mission: Mission) -> None:
        table = results_table(mission)

        if self._chat is None:
            # Deterministic fallback assessment.
            risk = "High" if mission.failures else "Low"
            mission.delivery_risk = risk
            mission.analysis = (
                f"{len(mission.failures)} of "
                f"{len(mission.report.outcomes) if mission.report else 0} tests failed."
            )
            mission.post(self.name, "Reporter", "analysis_ready",
                         f"Delivery risk {risk} (heuristic).")
            return

        prompt = build_analyst_prompt(mission.goal, table, mission.replan_count)
        try:
            resp = self._chat.chat.completions.create(
                model=azure_openai.deployment,
                messages=[
                    {"role": "system", "content": ANALYST_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content or "{}")
        except Exception as exc:
            logger.error("Analyst LLM call failed: %s", exc)
            mission.delivery_risk = "Medium"
            mission.analysis = f"Analyst error: {exc}"
            mission.post(self.name, "Reporter", "analysis_ready", "Analysis errored; see logs.")
            return

        mission.delivery_risk = str(data.get("delivery_risk", "Medium"))
        mission.analysis = str(data.get("analysis", "")).strip()

        replan = bool(data.get("replan_recommended")) and mission.replan_count < MAX_REPLANS
        if replan:
            mission.replan_requested = True
            mission.replan_guidance = str(data.get("replan_guidance", "")).strip()
            mission.replan_count += 1
            mission.post(
                self.name, "Planner", "replan_request",
                f"Failures look like flawed test steps, not bugs. Refine: "
                f"{mission.replan_guidance or 'clarify steps and expected outcomes.'}",
            )
        else:
            mission.post(
                self.name, "Reporter", "analysis_ready",
                f"Delivery risk {mission.delivery_risk}. {mission.analysis}",
            )
