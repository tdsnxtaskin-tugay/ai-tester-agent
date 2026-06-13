"""Planner agent — turns a high-level goal into concrete test cases.

Grounds the goal with Foundry IQ, then asks the LLM to produce a small JSON test
plan. Falls back to a single naive test case if the LLM is unavailable.
"""
from __future__ import annotations

import json
import logging

from ..config import azure_openai
from ..foundry_iq import FoundryIQClient
from ..pipeline import TestCase
from ..prompts import PLANNER_SYSTEM, build_planner_prompt
from .base import CollaboratingAgent, Mission

logger = logging.getLogger(__name__)


class PlannerAgent(CollaboratingAgent):
    name = "Planner"

    def __init__(self, chat_client, foundry: FoundryIQClient) -> None:
        self._chat = chat_client
        self._foundry = foundry

    async def act(self, mission: Mission) -> None:
        # Ground the goal once for the whole mission.
        ctx = self._foundry.ground(mission.goal, mission.replan_guidance or mission.goal)
        if ctx.grounded:
            mission.grounded_summary = ctx.answer
        grounded_block = ctx.as_prompt_block()

        cases = self._plan(mission, grounded_block)
        mission.test_cases = cases
        mission.replan_requested = False

        grounded_note = " (grounded by Foundry IQ)" if ctx.grounded else ""
        mission.post(
            self.name, "Tester", "plan_ready",
            f"Prepared {len(cases)} test case(s) for the goal{grounded_note}.",
        )

    def _plan(self, mission: Mission, grounded_block: str) -> list[TestCase]:
        if self._chat is None:
            logger.warning("Planner has no LLM; using a single fallback test case.")
            return [TestCase(
                feature=mission.goal,
                instructions=f"1. Open the application.\n2. Verify: {mission.goal}",
                test_case_title=mission.goal[:80],
            )]

        prompt = build_planner_prompt(
            goal=mission.goal,
            target_url=mission.target_url,
            grounded_block=grounded_block,
            guidance=mission.replan_guidance,
        )
        try:
            resp = self._chat.chat.completions.create(
                model=azure_openai.deployment,
                messages=[
                    {"role": "system", "content": PLANNER_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            items = data.get("test_cases", [])
            cases = [
                TestCase(
                    feature=i.get("feature", mission.goal),
                    instructions=i.get("instructions", ""),
                    test_case_title=i.get("test_case_title"),
                )
                for i in items if i.get("instructions")
            ]
            return cases or self._plan_fallback(mission)
        except Exception as exc:
            logger.error("Planner LLM call failed: %s", exc)
            return self._plan_fallback(mission)

    @staticmethod
    def _plan_fallback(mission: Mission) -> list[TestCase]:
        return [TestCase(
            feature=mission.goal,
            instructions=f"1. Open the application.\n2. Verify: {mission.goal}",
            test_case_title=mission.goal[:80],
        )]
