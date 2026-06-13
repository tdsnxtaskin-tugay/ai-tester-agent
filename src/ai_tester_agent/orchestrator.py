"""Multi-agent orchestrator — coordinates the collaborating agents.

Runs the collaboration:

    Planner -> Tester -> Analyst --(replan?)--> Planner -> Tester -> Analyst
                                  \\--(no)------> Reporter

The Analyst may request ONE replan if failures look like flawed test steps
rather than real bugs; otherwise control passes to the Reporter. All inter-agent
messages are recorded on the Mission so the collaboration is observable.
"""
from __future__ import annotations

import logging

from .agents.analyst import AnalystAgent
from .agents.base import Mission
from .agents.planner import PlannerAgent
from .agents.reporter import ReporterAgent
from .agents.tester import TesterAgent
from .foundry_iq import FoundryIQClient
from .llm import build_chat_client

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    def __init__(self, *, report_to_ado: bool = True) -> None:
        # Shared collaborators
        chat = self._try_chat()
        foundry = FoundryIQClient()

        self._planner = PlannerAgent(chat, foundry)
        self._tester = TesterAgent(report_to_ado=report_to_ado)
        self._analyst = AnalystAgent(chat)
        self._reporter = ReporterAgent(chat)

    @staticmethod
    def _try_chat():
        try:
            return build_chat_client()
        except Exception as exc:
            logger.warning("Chat client unavailable; agents will use fallbacks: %s", exc)
            return None

    async def run(self, mission: Mission) -> Mission:
        mission.post("Orchestrator", "team", "mission_start", mission.goal)

        # Round 1: plan -> test -> analyse
        await self._planner.act(mission)
        await self._tester.act(mission)
        await self._analyst.act(mission)

        # Optional bounded replan round driven by the Analyst's request
        if mission.replan_requested:
            mission.post("Orchestrator", "team", "replan", "Analyst requested a refined plan.")
            await self._planner.act(mission)
            await self._tester.act(mission)
            await self._analyst.act(mission)

        # Final reporting
        await self._reporter.act(mission)
        mission.post("Orchestrator", "team", "mission_done",
                     f"Risk={mission.delivery_risk or 'Unknown'}.")
        return mission
