# Demo Video Storyboard (≤ 5 minutes)

A tight script for the Agents League submission video. Use a **public** demo site as the
test target (e.g. a public docs site or a sample to-do app) — never an internal system.

## 0:00–0:30 — Hook & problem
- One line: "Manual UI testing is slow and brittle. AI Tester Agent reads plain-English
  test cases, drives a real browser, records video, and reports Pass/Fail to Azure
  DevOps — grounded by Foundry IQ."
- Show the project README on screen.

## 0:30–1:15 — Microsoft IQ (Foundry IQ)
- Show `docs/ARCHITECTURE.md` diagram.
- Explain: before each test, the agent asks **Foundry IQ** for grounded, cited knowledge
  about the feature so its reasoning is reliable. Point to `foundry_iq.py`.
- Show the `.env` keys `FOUNDRY_PROJECT_ENDPOINT` / `FOUNDRY_KNOWLEDGE_SOURCE` (values
  blurred).

## 1:15–1:40 — The test case
- Open `samples/sample_test_cases.json`. Read one case aloud (e.g. "Search returns
  relevant results").

## 1:40–3:30 — Live run
- Terminal: `python scripts/run_tester.py --source sample --no-ado`
  (or with `--source ado` if showing the ADO integration live).
- Narrate as logs stream:
  - "Foundry IQ grounding the feature…"
  - "browser-use driving the browser…" (show the browser window if not headless)
  - "LLM deciding Pass/Fail…"
  - "Transcoding the recording to mp4…"
- Show the printed summary: `[PASS] … [Foundry IQ] — reason`.

## 3:30–4:20 — Results in Azure DevOps
- Open the created **Test Run** in Azure DevOps.
- Show the result outcome, the comment (note the "[grounded by Foundry IQ]" tag), and the
  **attached video** recording.

## 4:20–5:00 — Wrap
- Recap the loop: grounded → executed → judged → recorded → reported.
- Mention reliability: every external step fails soft; nothing confidential in the repo.
- Show the public GitHub repo URL + MIT license.

## Recording tips
- Set `AGENT_HEADLESS=false` so the browser is visible during the run.
- Pre-warm dependencies (`playwright install chromium`) before recording.
- Keep secrets off-screen; use `.env.example` when showing config.
