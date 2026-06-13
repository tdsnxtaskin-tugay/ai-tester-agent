"""Shared contracts for the multi-agent collaboration.

`Mission` is the blackboard every agent reads from and writes to. `AgentMessage`
is how agents address each other; the message log makes the collaboration
observable (and demoable).
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..pipeline import PipelineReport, TestCase

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """A message from one agent to another (or to 'team')."""

    sender: str
    recipient: str
    intent: str
    content: str
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def render(self) -> str:
        return f"{self.sender} -> {self.recipient} [{self.intent}]: {self.content}"


@dataclass
class Mission:
    """Shared state passed between collaborating agents."""

    goal: str
    target_url: str | None = None

    # Filled in as agents collaborate
    grounded_summary: str = ""
    test_cases: list[TestCase] = field(default_factory=list)
    report: PipelineReport | None = None
    analysis: str = ""
    delivery_risk: str = ""
    summary: str = ""

    # Collaboration controls
    messages: list[AgentMessage] = field(default_factory=list)
    replan_requested: bool = False
    replan_guidance: str = ""
    replan_count: int = 0

    # Reporting
    report_to_ado: bool = True

    def post(self, sender: str, recipient: str, intent: str, content: str) -> AgentMessage:
        msg = AgentMessage(sender=sender, recipient=recipient, intent=intent, content=content)
        self.messages.append(msg)
        logger.info("✉️  %s", msg.render())
        return msg

    @property
    def failures(self) -> list:
        if not self.report:
            return []
        return [o for o in self.report.outcomes if o.verdict.outcome == "Failed"]


class CollaboratingAgent(ABC):
    """Base class for an agent that participates in a Mission."""

    name: str = "agent"

    @abstractmethod
    async def act(self, mission: Mission) -> None:
        """Read from and contribute to the shared Mission, posting messages."""
        raise NotImplementedError
