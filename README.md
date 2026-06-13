# 🤖 AI Tester Agent

[![CI](https://github.com/tdsnxtaskin-tugay/ai-tester-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/tdsnxtaskin-tugay/ai-tester-agent/actions/workflows/ci.yml)

> An autonomous web-testing agent for the **Microsoft Agents League @ AI Skills Fest 2026** — *Reasoning Agents* track, grounded by **Foundry IQ**.

AI Tester Agent reads natural-language test cases, **drives a real browser** with
[`browser-use`](https://github.com/browser-use/browser-use) to perform each step,
**records video** of the session, decides **Pass/Fail** with an LLM, and reports the
**results plus the recording** back to **Azure DevOps Test Runs** — helping teams keep
delivery quality high without writing brittle selectors by hand.

Every test is **grounded by Foundry IQ**: before the browser runs, the agent retrieves
cited, permission-aware knowledge about the feature (known flows, acceptance criteria,
prior defects) so its multi-step reasoning is reliable and explainable.

It runs in **two modes**:

- **single** — execute explicit test cases through the browser pipeline.
- **collaborate** — a **team of agents** (Planner → Tester → Analyst → Reporter) turns a
  high-level delivery goal into grounded, executed tests plus a delivery-quality report.
  The agents talk to each other over a shared *Mission* blackboard, and the **Analyst can
  ask the Planner to refine the plan** (a bounded replan loop) when failures look like
  flawed test steps rather than real bugs.

---

## ✨ What it does

1. **Loads test cases** from a JSON file or a saved Azure DevOps query.
2. **Grounds each test** with Foundry IQ (Microsoft IQ — required).
3. **Executes** the steps in a real browser via `browser-use` and **records video**.
4. **Judges** Pass/Fail by matching the agent's actions against the intended steps.
5. **Transcodes** the recording to `.mp4` (FFmpeg).
6. **Reports** results + attaches the video to an Azure DevOps Test Run.

## 🧠 Microsoft IQ — Foundry IQ (required)

Foundry IQ is Azure AI Foundry's agentic knowledge-retrieval layer. This agent queries
a configured **knowledge source** before each test to obtain grounded, **cited** context.
If Foundry IQ isn't configured, the agent **degrades gracefully** and still runs (clearly
logged) — but grounded runs are more accurate and are the intended mode for submission.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full flow and diagram.

## ✅ Prerequisites

- **Python 3.11+**
- **FFmpeg** on your `PATH` (for `.mp4` transcoding) — optional but recommended
- **Azure OpenAI** deployment (e.g. `gpt-4o-mini`)
- **Azure AI Foundry** project + knowledge source (for Foundry IQ)
- **Azure DevOps** PAT (only if you want results reported back to ADO)

## ⚙️ Setup

```bash
git clone <your-public-repo-url>
cd ai-tester-agent

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium --with-deps   # browser for browser-use

cp .env.example .env                # then fill in your own values
```

> ⚠️ Never commit your `.env`. Use **only public** demo apps as test targets — never
> internal/company systems.

## ▶️ Run

### Single-agent mode

```bash
# 1) Bundled public sample, no Azure DevOps reporting (great for a first run / demo):
python scripts/run_tester.py --mode single --source sample --no-ado

# 2) Your own JSON test cases, reporting results to Azure DevOps:
python scripts/run_tester.py --mode single --source json --file samples/sample_test_cases.json

# 3) Pull test cases straight from a saved Azure DevOps query:
python scripts/run_tester.py --mode single --source ado --query-id <GUID>
```

### Multi-agent collaboration mode

A team of agents turns a high-level goal into grounded, executed tests and a
delivery-quality report. The inter-agent conversation is printed at the end.

```bash
# From a high-level goal:
python scripts/run_tester.py --mode collaborate --goal "Users can search the docs and reach pricing" --no-ado

# From a mission file:
python scripts/run_tester.py --mode collaborate --mission samples/sample_mission.json
```

### Test-case JSON format

```json
[
  {
    "test_case_title": "Search returns relevant results",
    "feature": "Public docs site search",
    "instructions": "1. Open the site.\n2. Search for 'getting started'.\n3. Verify a relevant result appears."
  }
]
```

## 🗂️ Project structure

```
ai-tester-agent/
├── scripts/run_tester.py            # CLI entry point (single + collaborate modes)
├── samples/
│   ├── sample_test_cases.json       # public, non-confidential sample (single mode)
│   └── sample_mission.json          # high-level goal (collaborate mode)
├── docs/
│   ├── ARCHITECTURE.md              # architecture + Foundry IQ flow + diagram
│   └── DEMO_SCRIPT.md               # ≤5-min demo video storyboard
└── src/ai_tester_agent/
    ├── config.py                    # env-driven settings (no hard-coded values)
    ├── llm.py                       # Azure OpenAI clients
    ├── foundry_iq.py                # Foundry IQ grounded retrieval (Microsoft IQ)
    ├── browser_runner.py            # browser-use execution + video
    ├── video.py                     # FFmpeg transcode to .mp4
    ├── result_matcher.py            # LLM Pass/Fail verdict
    ├── azure_devops.py              # ADO REST: runs, results, attachments
    ├── test_loader.py               # load tests from JSON or ADO
    ├── prompts.py                   # prompt templates
    ├── pipeline.py                  # single-agent orchestration
    ├── orchestrator.py              # multi-agent collaboration coordinator
    └── agents/                      # collaborating agents
        ├── base.py                  # Mission blackboard + AgentMessage contract
        ├── planner.py               # goal -> test cases (grounded)
        ├── tester.py                # runs the browser pipeline
        ├── analyst.py               # delivery-quality + bounded replan loop
        └── reporter.py              # executive summary -> ADO
```

## 🔐 Safety & configuration

- All configuration comes from environment variables — **no secrets or company data**
  are committed. See [`.env.example`](.env.example).
- `browser-use` cloud sync and telemetry are disabled by default.
- Recordings, logs, and `.env` are git-ignored.

## 📄 License

MIT — see [`LICENSE`](LICENSE).
