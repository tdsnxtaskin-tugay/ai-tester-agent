"""Prompt templates for the browser agent task and result matching."""
from __future__ import annotations


def build_agent_task(feature: str, instructions: str, base_url: str | None,
                     grounded_block: str = "") -> str:
    """Compose the natural-language task handed to the browser-use agent."""
    parts = [
        "You are an autonomous QA tester driving a real web browser.",
        f"Feature under test: {feature}",
    ]
    if base_url:
        parts.append(f"Start at: {base_url}")
    parts.append("Execute these test steps exactly, in order:")
    parts.append(instructions.strip())
    if grounded_block:
        parts.append("")
        parts.append(grounded_block)
    parts.append("")
    parts.append(
        "After each step, observe the page and confirm the expected outcome. "
        "If a step cannot be completed, stop and clearly report which step "
        "failed and why. Do not invent UI that is not present."
    )
    return "\n".join(parts)


RESULT_MATCH_SYSTEM = (
    "You are a meticulous QA analyst. Given the intended test steps and the "
    "actions an automated browser agent actually performed, decide whether the "
    "test PASSED or FAILED. Be strict: a test only passes if every expected "
    "outcome was observably achieved. Respond ONLY with compact JSON of the "
    'form {"outcome": "Passed|Failed", "reason": "<one sentence>", '
    '"failed_step": <step number or null>}.'
)


def build_result_match_prompt(feature: str, instructions: str,
                              agent_history: str) -> str:
    return (
        f"Feature: {feature}\n\n"
        f"Intended test steps:\n{instructions}\n\n"
        f"What the browser agent actually did:\n{agent_history}\n\n"
        "Return the JSON verdict now."
    )


# --- Multi-agent collaboration prompts ------------------------------------

PLANNER_SYSTEM = (
    "You are a QA Planner agent. Turn a high-level delivery goal into a small set "
    "of concrete, independent UI test cases a browser agent can execute. Each test "
    "must have numbered, observable steps and a clear expected outcome. Respond ONLY "
    'with JSON: {"test_cases": [{"test_case_title": "...", "feature": "...", '
    '"instructions": "1. ...\\n2. ..."}]}. Produce 1-4 focused test cases.'
)


def build_planner_prompt(goal: str, target_url: str | None,
                         grounded_block: str = "", guidance: str = "") -> str:
    parts = [f"Delivery goal: {goal}"]
    if target_url:
        parts.append(f"Target application URL: {target_url}")
    if grounded_block:
        parts.append("")
        parts.append(grounded_block)
    if guidance:
        parts.append("")
        parts.append(f"Refinement guidance from the Analyst agent: {guidance}")
    parts.append("")
    parts.append("Return the JSON test plan now.")
    return "\n".join(parts)


ANALYST_SYSTEM = (
    "You are a Delivery Quality Analyst agent. Given a goal and the results of "
    "automated browser tests, assess delivery quality and decide whether failures "
    "indicate real product bugs or ambiguous/flawed test steps that should be "
    "replanned. Be decisive. Respond ONLY with JSON: "
    '{"delivery_risk": "Low|Medium|High", "likely_real_bugs": true|false, '
    '"replan_recommended": true|false, "replan_guidance": "<empty if none>", '
    '"analysis": "<2-4 sentence assessment>"}.'
)


def build_analyst_prompt(goal: str, results_table: str, replan_count: int) -> str:
    return (
        f"Delivery goal: {goal}\n\n"
        f"Test results:\n{results_table}\n\n"
        f"Replans already performed: {replan_count} (max 1 allowed).\n"
        "Assess and return the JSON now."
    )


REPORTER_SYSTEM = (
    "You are a Reporter agent. Write a concise, executive delivery-quality summary "
    "(max 6 sentences) from the goal, test results, and analyst assessment. Be "
    "factual and actionable. Plain text only."
)


def build_reporter_prompt(goal: str, results_table: str, analysis: str,
                          delivery_risk: str) -> str:
    return (
        f"Delivery goal: {goal}\n\n"
        f"Test results:\n{results_table}\n\n"
        f"Analyst assessment (risk={delivery_risk}): {analysis}\n\n"
        "Write the summary now."
    )
