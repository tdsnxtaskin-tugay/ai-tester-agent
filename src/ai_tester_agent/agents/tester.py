"""Tester agent — runs the planned test cases through the browser pipeline.

Wraps the existing single-agent `TesterPipeline` so the browser execution,
Foundry IQ grounding per test, video recording, and (optional) Azure DevOps
reporting are reused unchanged.
"""
from __future__ import annotations

import logging

from ..pipeline import TesterPipeline
from .base import CollaboratingAgent, Mission

logger = logging.getLogger(__name__)


class TesterAgent(CollaboratingAgent):
    name = "Tester"

    def __init__(self, *, report_to_ado: bool = True) -> None:
        self._report_to_ado = report_to_ado
        self._pipeline: TesterPipeline | None = None

    def _get_pipeline(self) -> TesterPipeline:
        # Build lazily: constructing the pipeline initializes the browser LLM.
        if self._pipeline is None:
            self._pipeline = TesterPipeline(report_to_ado=self._report_to_ado)
        return self._pipeline

    async def act(self, mission: Mission) -> None:
        if not mission.test_cases:
            mission.post(self.name, "team", "no_tests", "No test cases to run.")
            return

        report = await self._get_pipeline().run(mission.test_cases)
        mission.report = report

        mission.post(
            self.name, "Analyst", "tests_done",
            f"Executed {len(report.outcomes)} test(s): "
            f"{report.passed} passed, {report.failed} failed. "
            f"Recordings captured and results reported.",
        )
