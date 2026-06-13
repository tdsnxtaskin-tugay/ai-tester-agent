"""Multi-agent collaboration layer.

A small team of specialised agents that talk to each other and take action to
turn a high-level delivery goal into executed, grounded browser tests and a
delivery-quality report:

    Planner -> Tester -> Analyst -> Reporter

They share a Foundry IQ knowledge backbone and communicate via messages posted
on a shared `Mission` blackboard, coordinated by `MultiAgentOrchestrator`.
"""

from .base import AgentMessage, CollaboratingAgent, Mission

__all__ = ["AgentMessage", "CollaboratingAgent", "Mission"]
