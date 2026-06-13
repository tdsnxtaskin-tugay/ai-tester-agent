"""Reporter agent — composes the final delivery-quality summary.

Produces an executive summary from the goal, results, and analyst assessment.
Uses the LLM for polish when available, with a deterministic fallback, and can
post the summary back to the Azure DevOps Test Run as a comment.
"""
from __future__ import annotations

import logging

from ..config import azure_openai
from ..prompts import REPORTER_SYSTEM, build_reporter_prompt
from .analyst import results_table
from .base import CollaboratingAgent, Mission

logger = logging.getLogger(__name__)


class ReporterAgent(CollaboratingAgent):
    name = "Reporter"

    def __init__(self, chat_client) -> None:
        self._chat = chat_client

    async def act(self, mission: Mission) -> None:
        table = results_table(mission)
        summary = self._summarize(mission, table)
        mission.summary = summary

        mission.post(self.name, "team", "report_ready",
                     "Delivery-quality summary ready.")

        if mission.report_to_ado:
            self._post_to_ado(mission, summary)

    def _summarize(self, mission: Mission, table: str) -> str:
        passed = mission.report.passed if mission.report else 0
        failed = mission.report.failed if mission.report else 0
        deterministic = (
            f"Goal: {mission.goal}\n"
            f"Result: {passed} passed, {failed} failed. "
            f"Delivery risk: {mission.delivery_risk or 'Unknown'}.\n"
            f"{mission.analysis}"
        )
        if self._chat is None:
            return deterministic
        try:
            resp = self._chat.chat.completions.create(
                model=azure_openai.deployment,
                messages=[
                    {"role": "system", "content": REPORTER_SYSTEM},
                    {"role": "user", "content": build_reporter_prompt(
                        mission.goal, table, mission.analysis, mission.delivery_risk)},
                ],
                temperature=0.3,
            )
            return (resp.choices[0].message.content or deterministic).strip()
        except Exception as exc:
            logger.error("Reporter LLM call failed: %s", exc)
            return deterministic

    @staticmethod
    def _post_to_ado(mission: Mission, summary: str) -> None:
        if not mission.report or not mission.report.ado_run_id:
            return
        try:
            from ..azure_devops import AzureDevOpsClient

            client = AzureDevOpsClient()
            client.add_test_result(
                mission.report.ado_run_id,
                test_case_title=f"Delivery summary — {mission.goal[:60]}",
                outcome="Passed" if mission.report.failed == 0 else "Failed",
                comment=summary,
            )
            logger.info("Posted delivery summary to ADO run %s.", mission.report.ado_run_id)
        except Exception as exc:
            logger.warning("Could not post summary to ADO: %s", exc)
