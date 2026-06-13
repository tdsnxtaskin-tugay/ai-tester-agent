#!/usr/bin/env python3
"""AI Tester Agent — CLI entry point.

Two modes:
  * single      — run explicit test cases through the browser pipeline.
  * collaborate — a team of agents (Planner -> Tester -> Analyst -> Reporter)
                  turns a high-level goal into grounded, executed tests plus a
                  delivery-quality report.

Examples:
    # Single-agent: run the bundled public sample, no Azure DevOps reporting:
    python scripts/run_tester.py --mode single --source sample --no-ado

    # Single-agent: run from a JSON file and report results to Azure DevOps:
    python scripts/run_tester.py --mode single --source json --file samples/sample_test_cases.json

    # Single-agent: pull test cases from a saved Azure DevOps query:
    python scripts/run_tester.py --mode single --source ado

    # Multi-agent collaboration from a high-level goal:
    python scripts/run_tester.py --mode collaborate --goal "Users can search the docs" --no-ado

    # Multi-agent collaboration from a mission file:
    python scripts/run_tester.py --mode collaborate --mission samples/sample_mission.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import platform
import sys
from pathlib import Path

# Make the src/ package importable when run directly.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI Tester Agent")
    p.add_argument("--mode", choices=["single", "collaborate"], default="single",
                   help="Run a single tester or the multi-agent collaboration.")
    # single-mode options
    p.add_argument("--source", choices=["sample", "json", "ado"], default="sample",
                   help="[single] Where to load test cases from.")
    p.add_argument("--file", help="[single] Path to a JSON test-case file (--source json).")
    p.add_argument("--query-id", help="[single] Azure DevOps saved query id (--source ado).")
    # collaborate-mode options
    p.add_argument("--goal", help="[collaborate] High-level delivery goal to test.")
    p.add_argument("--mission", help="[collaborate] Path to a mission JSON file.")
    p.add_argument("--url", help="[collaborate] Target application URL (overrides mission/env).")
    # shared
    p.add_argument("--no-ado", action="store_true",
                   help="Do not report results back to Azure DevOps.")
    return p.parse_args()


async def _run_single(args) -> int:
    from ai_tester_agent import test_loader
    from ai_tester_agent.pipeline import TesterPipeline

    if args.source == "sample":
        default = Path(__file__).resolve().parents[1] / "samples" / "sample_test_cases.json"
        cases = test_loader.load_from_json(default)
    elif args.source == "json":
        if not args.file or not os.path.exists(args.file):
            print("ERROR: --file is required and must exist for --source json.")
            return 2
        cases = test_loader.load_from_json(args.file)
    else:  # ado
        cases = test_loader.load_from_ado(args.query_id)

    if not cases:
        print("No test cases to run.")
        return 0

    pipeline = TesterPipeline(report_to_ado=not args.no_ado)
    report = await pipeline.run(cases)

    print("\n===== AI Tester Agent — Summary =====")
    for o in report.outcomes:
        flag = "PASS" if o.verdict.outcome == "Passed" else "FAIL"
        grounded = " [Foundry IQ]" if o.grounded else ""
        print(f"[{flag}] {o.test_case.title}{grounded} — {o.verdict.reason}")
    print(f"\n{report.passed} passed, {report.failed} failed.")
    if report.ado_run_id:
        print(f"Azure DevOps Test Run: {report.ado_run_id}")
    return 0 if report.failed == 0 else 1


async def _run_collaborate(args) -> int:
    from ai_tester_agent.agents.base import Mission
    from ai_tester_agent.config import agent as agent_cfg
    from ai_tester_agent.orchestrator import MultiAgentOrchestrator

    goal = args.goal
    target_url = args.url or agent_cfg.target_base_url
    if args.mission:
        if not os.path.exists(args.mission):
            print("ERROR: --mission file does not exist.")
            return 2
        data = json.loads(Path(args.mission).read_text(encoding="utf-8"))
        goal = goal or data.get("goal")
        target_url = args.url or data.get("target_url") or target_url
    if not goal:
        print("ERROR: provide --goal or --mission for collaborate mode.")
        return 2

    mission = Mission(goal=goal, target_url=target_url, report_to_ado=not args.no_ado)
    orchestrator = MultiAgentOrchestrator(report_to_ado=not args.no_ado)
    await orchestrator.run(mission)

    print("\n===== Multi-Agent Collaboration — Conversation =====")
    for m in mission.messages:
        print(m.render())

    print("\n===== Test Results =====")
    if mission.report:
        for o in mission.report.outcomes:
            flag = "PASS" if o.verdict.outcome == "Passed" else "FAIL"
            grounded = " [Foundry IQ]" if o.grounded else ""
            print(f"[{flag}] {o.test_case.title}{grounded} — {o.verdict.reason}")
        print(f"\n{mission.report.passed} passed, {mission.report.failed} failed.")
        if mission.report.ado_run_id:
            print(f"Azure DevOps Test Run: {mission.report.ado_run_id}")

    print("\n===== Delivery-Quality Summary =====")
    print(f"Risk: {mission.delivery_risk or 'Unknown'}")
    print(mission.summary)
    failed = mission.report.failed if mission.report else 1
    return 0 if failed == 0 else 1


async def _amain() -> int:
    args = _parse_args()
    _configure_logging()

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if args.mode == "collaborate":
        return await _run_collaborate(args)
    return await _run_single(args)


def main() -> None:
    try:
        raise SystemExit(asyncio.run(_amain()))
    except KeyboardInterrupt:
        print("Interrupted.")
        raise SystemExit(130)


if __name__ == "__main__":
    main()

