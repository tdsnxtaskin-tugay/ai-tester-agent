# Submission — Project 2: Agent Guild (Multi-Agent Delivery Quality)

> Copy-paste these fields into the Innovation Studio project page. All content is
> public-safe (no company, customer, or confidential information).

## Title (max 140)
Agent Guild: Multi-Agent Delivery-Quality Collaboration with Foundry IQ

## Tagline (max 300)
A team of AI agents — Planner, Tester, Analyst, and Reporter — collaborate over a shared mission to turn a high-level goal into grounded browser tests and a delivery-quality report. They plan, test, debate, replan, and act — all grounded by Foundry IQ.

## Keywords / Tags
Multi-Agent, Agentic AI, Foundry IQ, Reasoning, Orchestration, Delivery Quality, QA Automation, Azure DevOps, Azure OpenAI, Python

## Challenge
🧠 Reasoning Agents (Microsoft Foundry)
*(Integrates Microsoft IQ: **Foundry IQ** — required.)*

## Writing code as part of this project?
Yes

## Code Repository
Add after saving: `https://github.com/<your-username>/ai-tester-agent`

## Open for others to join?
Optional — set as you prefer.

## Skills needed (if open to join)
Python, multi-agent orchestration, Azure AI Foundry, LLM prompt design, QA automation

---

## Description (Markdown)

### The problem
Shipping with confidence means answering "is this feature actually working, and what's
the delivery risk?" That requires planning the right tests, running them, interpreting
failures (real bug vs. flawed test), and summarizing risk — work usually split across
several people and tools.

### The solution
**Agent Guild** is a team of specialised AI agents that collaborate to answer that
question end-to-end from a single high-level goal:

```
Planner ──▶ Tester ──▶ Analyst ──(replan?)──▶ Planner ...
                              └──(no)──▶ Reporter ──▶ Azure DevOps
```

- **Planner** grounds the goal with **Foundry IQ** and produces concrete test cases.
- **Tester** runs them in a real browser (browser-use), records video, reports to Azure DevOps.
- **Analyst** assesses delivery risk and decides whether failures are real bugs or
  flawed test steps — and can **send a replan request back to the Planner**.
- **Reporter** writes an executive delivery-quality summary and posts it to the test run.

The agents communicate via messages on a shared **Mission blackboard**; the full
conversation is printed, so the collaboration is observable and demoable.

### Multi-step reasoning (the heart of this track)
This is not a fixed pipeline. The **Analyst can ask the Planner to refine the plan**
(a bounded, one-round feedback loop) when failures look like ambiguous test steps rather
than product defects. The agents negotiate, take corrective action, and converge on a
grounded verdict — demonstrating genuine multi-agent, multi-step reasoning.

### Microsoft IQ — Foundry IQ (required)
Foundry IQ is the shared knowledge backbone every agent reasons over. The Planner grounds
the goal with cited knowledge, and that grounding flows through testing, analysis, and the
final report — keeping the whole guild's reasoning factual, explainable, and
permission-aware.

### Why it's original
- A small, legible **agent society** (plan → test → analyse → report) with a real
  feedback loop, not just chained prompts.
- Grounded retrieval shared across every agent via Foundry IQ.
- Produces an executive **delivery-quality** verdict, not just test logs.

### Reliability & safety
- Bounded replan loop (max 1) — deterministic and safe, no runaway loops.
- Every agent degrades gracefully without an LLM (fallback plan, heuristic risk).
- External steps fail soft; secrets externalized; nothing confidential in the repo.

### Tech stack
Python 3.11+ · Azure AI Foundry (Foundry IQ) · Azure OpenAI · browser-use ·
Playwright/Chromium · Azure DevOps REST API · FFmpeg.

### Try it
```bash
pip install -r requirements.txt
playwright install chromium --with-deps
cp .env.example .env   # fill in your own values
python scripts/run_tester.py --mode collaborate --mission samples/sample_mission.json --no-ado
```

### Demo
The inter-agent conversation prints at the end of a run. Architecture and the multi-agent
diagram are in `docs/ARCHITECTURE.md`; the video storyboard is in `docs/DEMO_SCRIPT.md`.
