# Submission — Project 1: AI Tester Agent

> Copy-paste these fields into the Innovation Studio project page. All content is
> public-safe (no company, customer, or confidential information).

## Title (max 140)
AI Tester Agent: Autonomous Browser QA Grounded by Foundry IQ

## Tagline (max 300)
AI Tester Agent reads plain-English test cases, drives a real browser with browser-use, records video, and reports Pass/Fail back to Azure DevOps — every test grounded by Foundry IQ for reliable, explainable, multi-step reasoning. QA that scales without brittle selectors.

## Keywords / Tags
AI Agent, Foundry IQ, browser-use, QA Automation, Test Automation, Azure DevOps, Azure OpenAI, Playwright, Python, GitHub Copilot

## Challenge
🎨 Creative Apps (GitHub Copilot)
*(Integrates Microsoft IQ: **Foundry IQ** — required.)*

## Writing code as part of this project?
Yes

## Code Repository
Add after saving: `https://github.com/<your-username>/ai-tester-agent`

## Open for others to join?
Optional — set as you prefer.

## Skills needed (if open to join)
Python, Azure OpenAI, browser automation, QA/test automation, Azure DevOps

---

## Description (Markdown)

### The problem
Manual UI testing is slow, repetitive, and brittle. Traditional automated UI tests
break whenever selectors or layouts change, and writing them by hand consumes hours of
engineering time that could go into shipping features.

### The solution
**AI Tester Agent** turns plain-English test cases into executed, video-recorded browser
tests and reports the results straight into **Azure DevOps Test Runs** — no brittle
selectors required.

For every test it:
1. **Grounds** the feature with **Foundry IQ** — retrieving cited, permission-aware
   knowledge (known flows, acceptance criteria, prior defects) before acting.
2. **Executes** the steps in a real browser with
   [`browser-use`](https://github.com/browser-use/browser-use) and **records video**.
3. **Judges** Pass/Fail with a strict LLM verdict that compares intended steps to what
   the agent actually did.
4. **Transcodes** the recording to `.mp4` (FFmpeg).
5. **Reports** the result and **attaches the video** to an Azure DevOps Test Run.

### Microsoft IQ — Foundry IQ (required)
Foundry IQ is Azure AI Foundry's agentic knowledge-retrieval layer. Before the browser
runs, the agent queries a configured knowledge source to ground its reasoning with cited
answers. This reduces hallucinated steps and makes each verdict explainable — the
Pass/Fail comment posted to Azure DevOps notes when a result was grounded by Foundry IQ.
If Foundry IQ is unavailable, the agent degrades gracefully and still runs.

### Why it's original
- Combines autonomous browser agents + grounded retrieval + native Azure DevOps test
  reporting in one loop.
- Treats the recording as a first-class deliverable attached to the test result.
- No hand-written selectors: tests are natural language, executed by reasoning.

### Reliability & safety
- Every external step (Foundry IQ, FFmpeg, Azure DevOps) **fails soft** — a missing
  optional dependency is logged and skipped, never crashing a run.
- Strict temperature-0 JSON verdicts for deterministic Pass/Fail.
- browser-use cloud sync and telemetry disabled by default.
- All secrets/config externalized to `.env`; nothing confidential in the repo.

### Tech stack
Python 3.11+ · browser-use · Playwright/Chromium · Azure OpenAI · Azure AI Foundry
(Foundry IQ) · Azure DevOps REST API · FFmpeg. Built with GitHub Copilot.

### Try it
```bash
pip install -r requirements.txt
playwright install chromium --with-deps
cp .env.example .env   # fill in your own values
python scripts/run_tester.py --mode single --source sample --no-ado
```

### Demo
See `docs/DEMO_SCRIPT.md` for the ≤5-minute video storyboard. Architecture and the
Foundry IQ flow are in `docs/ARCHITECTURE.md`.
