"""Pipeline — ties the whole flow together for one or more test cases.

For each test case:
  1. Foundry IQ grounds the feature with cited knowledge.
  2. browser-use drives a real browser through the steps and records video.
  3. GPT matches the agent's actions to the intended steps -> Pass/Fail.
  4. The recording is transcoded to .mp4.
  5. Results + video are reported back to an Azure DevOps Test Run (optional).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import config
from .browser_runner import BrowserRunner
from .foundry_iq import FoundryIQClient
from .llm import build_browser_llm, build_chat_client
from .result_matcher import ResultMatcher, Verdict
from .video import to_mp4

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    feature: str
    instructions: str
    test_case_title: str | None = None

    @property
    def title(self) -> str:
        return self.test_case_title or self.feature


@dataclass
class TestOutcome:
    test_case: TestCase
    verdict: Verdict
    grounded: bool
    recording_path: str | None = None


@dataclass
class PipelineReport:
    started_at: str
    outcomes: list[TestOutcome] = field(default_factory=list)
    ado_run_id: int | None = None

    @property
    def passed(self) -> int:
        return sum(1 for o in self.outcomes if o.verdict.outcome == "Passed")

    @property
    def failed(self) -> int:
        return sum(1 for o in self.outcomes if o.verdict.outcome == "Failed")


class TesterPipeline:
    def __init__(self, *, report_to_ado: bool = True) -> None:
        self._foundry = FoundryIQClient()
        self._browser = BrowserRunner(build_browser_llm())
        self._matcher = ResultMatcher(build_chat_client())
        self._report_to_ado = report_to_ado
        self._ado = None
        if report_to_ado:
            try:
                from .azure_devops import AzureDevOpsClient
                self._ado = AzureDevOpsClient()
            except Exception as exc:
                logger.warning("ADO reporting disabled: %s", exc)
                self._report_to_ado = False

    async def run(self, test_cases: list[TestCase]) -> PipelineReport:
        report = PipelineReport(started_at=datetime.now(timezone.utc).isoformat())

        run_id = None
        if self._report_to_ado and self._ado:
            run_name = f"AI Tester Agent {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            run_id = self._ado.create_test_run(run_name, config.azure_devops.plan_id or None)
            report.ado_run_id = run_id

        for tc in test_cases:
            outcome = await self._run_one(tc, run_id)
            report.outcomes.append(outcome)

        if self._report_to_ado and self._ado and run_id:
            self._ado.complete_test_run(run_id)

        logger.info("Done: %s passed, %s failed.", report.passed, report.failed)
        return report

    async def _run_one(self, tc: TestCase, run_id: int | None) -> TestOutcome:
        logger.info("--- Testing: %s ---", tc.title)

        # 1. Foundry IQ grounding
        ctx = self._foundry.ground(tc.feature, tc.instructions)
        grounded_block = ctx.as_prompt_block()

        # 2. Browser execution + recording
        run = await self._browser.run_test(
            feature=tc.feature,
            instructions=tc.instructions,
            grounded_block=grounded_block,
        )

        # 3. Result matching
        verdict = self._matcher.evaluate(
            feature=tc.feature,
            instructions=tc.instructions,
            agent_history=run.history_text,
            run_completed=run.completed,
        )

        # 4. Video transcode
        mp4_path = None
        if run.recording_path:
            result = to_mp4(run.recording_path, config.PROCESSED_VIDEO_DIR)
            mp4_path = str(result) if result else None

        # 5. ADO reporting
        if self._report_to_ado and self._ado and run_id:
            comment = verdict.reason
            if ctx.grounded:
                comment += "  [grounded by Foundry IQ]"
            self._ado.add_test_result(
                run_id,
                test_case_title=tc.title,
                outcome=verdict.outcome,
                comment=comment,
            )
            if mp4_path:
                self._ado.attach_video_to_run(run_id, mp4_path)

        return TestOutcome(
            test_case=tc,
            verdict=verdict,
            grounded=ctx.grounded,
            recording_path=mp4_path,
        )
