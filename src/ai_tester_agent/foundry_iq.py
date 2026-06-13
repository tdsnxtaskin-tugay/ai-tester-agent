"""Foundry IQ integration — grounded knowledge retrieval (REQUIRED Microsoft IQ layer).

Before the browser agent runs a test, we ask Foundry IQ for grounded, cited
context about the feature under test (known flows, selectors, acceptance
criteria, prior defects). This reduces hallucination and makes the agent's
multi-step reasoning more reliable.

Foundry IQ is Azure AI Foundry's agentic knowledge-retrieval layer: it connects
multiple enterprise knowledge sources, enforces permissions, and returns
grounded answers with citations. We query it through the Azure AI Projects SDK.

If Foundry IQ is not configured, retrieval degrades gracefully to an empty
context so the agent can still run (clearly logged).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .config import foundry_iq

logger = logging.getLogger(__name__)


@dataclass
class GroundedContext:
    """Grounded knowledge returned by Foundry IQ for a single test."""

    query: str
    answer: str = ""
    citations: list[str] = field(default_factory=list)
    grounded: bool = False

    def as_prompt_block(self) -> str:
        """Render the grounded context for injection into an agent prompt."""
        if not self.grounded or not self.answer:
            return ""
        lines = ["Grounded knowledge (from Foundry IQ):", self.answer.strip()]
        if self.citations:
            lines.append("Sources: " + "; ".join(self.citations))
        return "\n".join(lines)


class FoundryIQClient:
    """Thin wrapper over Azure AI Foundry knowledge retrieval (Foundry IQ)."""

    def __init__(self) -> None:
        self._settings = foundry_iq
        self._project = None
        if self._settings.configured:
            self._connect()
        else:
            logger.warning(
                "Foundry IQ not configured (FOUNDRY_PROJECT_ENDPOINT missing). "
                "Test runs will proceed WITHOUT grounded context."
            )

    def _connect(self) -> None:
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential

            self._project = AIProjectClient(
                endpoint=self._settings.project_endpoint,
                credential=DefaultAzureCredential(),
            )
            logger.info(
                "Foundry IQ connected (knowledge_source=%s).",
                self._settings.knowledge_source,
            )
        except Exception as exc:  # pragma: no cover - depends on live Azure creds
            logger.error("Failed to connect to Foundry IQ: %s", exc)
            self._project = None

    @property
    def available(self) -> bool:
        return self._project is not None

    def ground(self, feature: str, instructions: str) -> GroundedContext:
        """Retrieve grounded context for the feature/test about to be executed.

        Args:
            feature:      Short feature / user story title.
            instructions: The natural-language test steps.

        Returns:
            GroundedContext — empty (grounded=False) if Foundry IQ is unavailable.
        """
        query = (
            f"What should a tester know to reliably verify this feature?\n"
            f"Feature: {feature}\nTest steps: {instructions}"
        )
        if not self.available:
            return GroundedContext(query=query, grounded=False)

        try:
            answer, citations = self._retrieve(query)
            return GroundedContext(
                query=query,
                answer=answer,
                citations=citations,
                grounded=bool(answer),
            )
        except Exception as exc:  # pragma: no cover - depends on live service
            logger.error("Foundry IQ retrieval failed: %s", exc)
            return GroundedContext(query=query, grounded=False)

    def _retrieve(self, query: str) -> tuple[str, list[str]]:
        """Run a knowledge-retrieval query against the configured Foundry IQ source.

        Uses the Azure AI Projects knowledge-retrieval API. The exact call shape
        depends on your Foundry project configuration; this method centralizes it
        so the rest of the agent stays decoupled from the SDK surface.
        """
        retrieval = self._project.knowledge_retrieval.retrieve(  # type: ignore[union-attr]
            knowledge_source=self._settings.knowledge_source,
            query=query,
        )
        answer = getattr(retrieval, "answer", "") or ""
        citations = [
            getattr(c, "url", "") or getattr(c, "title", "")
            for c in getattr(retrieval, "citations", []) or []
        ]
        return answer, [c for c in citations if c]
