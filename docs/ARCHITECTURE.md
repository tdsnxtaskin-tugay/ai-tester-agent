# Architecture — AI Tester Agent

## Purpose

Turn natural-language test cases into **executed, video-recorded, grounded** browser
tests whose results flow back into Azure DevOps — built for the *Reasoning Agents* track
and grounded by **Foundry IQ**.

## End-to-end flow

```
            ┌──────────────────────────────────────────────────────────┐
            │                     Test sources                         │
            │   samples/*.json            Azure DevOps saved query     │
            └───────────────┬───────────────────────┬──────────────────┘
                            │ test_loader            │
                            ▼                        ▼
                       ┌───────────────────────────────────┐
                       │            TestCase[]              │
                       └─────────────────┬─────────────────┘
                                         │  pipeline.TesterPipeline
                       ┌─────────────────▼─────────────────┐
                       │  For each test case:               │
                       │                                    │
   ┌───────────────┐   │  1. Foundry IQ.ground(feature)     │   grounded, cited
   │  Foundry IQ   │◀──┼─────────────────────────────────── │   knowledge
   │ knowledge src │──▶│     -> GroundedContext             │
   └───────────────┘   │                                    │
                       │  2. BrowserRunner.run_test()       │   real browser +
   ┌───────────────┐   │     (browser-use Agent + video)    │   .webm/.mkv recording
   │ Azure OpenAI  │◀──┼─────────────────────────────────── │
   │ (ChatAzure-   │   │                                    │
   │  OpenAI LLM)  │   │  3. ResultMatcher.evaluate()       │   strict Pass/Fail
   └───────────────┘   │     (Azure OpenAI JSON verdict)    │   + reason
                       │                                    │
                       │  4. video.to_mp4() (FFmpeg)        │   shareable .mp4
                       │                                    │
                       │  5. AzureDevOpsClient:             │
                       │     create_test_run / add_result / │
                       │     attach_video / complete        │
                       └─────────────────┬──────────────────┘
                                         ▼
                            ┌─────────────────────────┐
                            │   Azure DevOps Test Run │
                            │   results + video       │
                            └─────────────────────────┘
```

## Components

| Module | Responsibility |
|---|---|
| `config.py` | Loads all settings from env/`.env`. No hard-coded company values. |
| `foundry_iq.py` | **Foundry IQ** client — grounded, cited knowledge per test. Degrades gracefully if unconfigured. |
| `llm.py` | Builds the `browser-use` ChatAzureOpenAI model and a plain Azure OpenAI chat client. |
| `browser_runner.py` | Runs one test in a real browser via `browser-use`, records video. |
| `result_matcher.py` | Asks Azure OpenAI for a strict JSON Pass/Fail verdict. |
| `video.py` | Transcodes raw recordings to `.mp4` with FFmpeg (graceful fallback). |
| `azure_devops.py` | Minimal ADO REST client: queries, test runs, results, attachments. |
| `test_loader.py` | Loads `TestCase[]` from JSON or an ADO saved query. |
| `pipeline.py` | Orchestrates grounding → execution → verdict → video → reporting. |

## How Foundry IQ makes this a *reasoning* agent

- **Grounding before acting:** the agent retrieves cited knowledge about the feature
  before it touches the browser, reducing hallucinated steps.
- **Explainability:** the Pass/Fail comment posted to Azure DevOps notes when a verdict
  was grounded by Foundry IQ, with sources available from the knowledge source.
- **Permission-aware:** Foundry IQ enforces access controls on the underlying knowledge,
  so the agent only reasons over data it is allowed to see.

## Reliability & safety (judging: 20%)

- Foundry IQ retrieval, FFmpeg transcode, and ADO reporting all **fail soft** — a missing
  optional dependency never crashes a run; it is logged and skipped.
- `browser-use` cloud sync + telemetry disabled by default.
- Strict, temperature-0 JSON verdicts for deterministic Pass/Fail.
- All secrets/config externalized to `.env`; nothing confidential in the repo.

---

## Multi-agent collaboration (collaborate mode)

A team of specialised agents turns a high-level delivery goal into grounded, executed
tests plus a delivery-quality report. They share a `Mission` blackboard and communicate
via `AgentMessage`s (the conversation is printed and demoable).

```
   goal ──▶ ┌─────────────────────────── MultiAgentOrchestrator ───────────────────────────┐
            │                                                                               │
            │   ┌──────────┐  plan_ready   ┌──────────┐  tests_done   ┌──────────┐          │
            │   │ Planner  │ ────────────▶ │  Tester  │ ────────────▶ │ Analyst  │          │
            │   └────▲─────┘               └──────────┘               └────┬─────┘          │
            │        │ replan_request (≤1, if failures look like              │              │
            │        └──────────────────  flawed test steps, not bugs)       │ analysis_ready│
            │                                                                 ▼              │
            │                                                          ┌──────────┐          │
            │                                                          │ Reporter │ ──▶ ADO  │
            │                                                          └──────────┘ summary  │
            └───────────────────────────────────────────────────────────────────────────────┘
                         every agent grounds via the shared Foundry IQ backbone
```

| Agent | Role |
|---|---|
| **Planner** (`agents/planner.py`) | Grounds the goal with Foundry IQ, produces 1–4 concrete test cases. |
| **Tester** (`agents/tester.py`) | Runs the test cases through the single-agent `TesterPipeline` (browser + video + ADO). |
| **Analyst** (`agents/analyst.py`) | Assesses delivery risk; decides if failures are real bugs or flawed steps, and may request **one** replan. |
| **Reporter** (`agents/reporter.py`) | Writes an executive delivery-quality summary and posts it to the ADO Test Run. |

**Why this is genuine collaboration, not a fixed pipeline:** the Analyst can send a
`replan_request` back to the Planner with concrete guidance, causing a second
plan→test→analyse round. This bounded feedback loop (max 1 replan) demonstrates
multi-step, multi-agent reasoning while staying deterministic and safe.

All agents degrade gracefully: with no LLM, the Planner emits a fallback test case, and
the Analyst/Reporter produce heuristic/deterministic output — the collaboration still
completes.
