# Pre-Submission Compliance Checklist

Run through this for **each** project before submitting to the Agents League.

## Confidential information (CRITICAL — public repo)
- [ ] No company / employer names, internal URLs, org/project/team names
- [ ] No customer data or PII
- [ ] No credentials, API keys, tokens, passwords, or secrets committed
- [ ] No proprietary/internal code or pre-release/NDA content
- [ ] `.env` is git-ignored; only `.env.example` with placeholders is committed
- [ ] Test targets are **public** demo apps, never internal systems

## Required submission contents
- [ ] Public GitHub repository with a complete `README.md`
- [ ] Microsoft IQ integration present and documented (**Foundry IQ**)
- [ ] Architecture diagram (`docs/ARCHITECTURE.md`)
- [ ] Demo video ≤ 5 min uploaded to YouTube/Vimeo (storyboard: `docs/DEMO_SCRIPT.md`)
- [ ] Project description, tagline, keywords, and Challenge selected
- [ ] Original work; all rights/licenses obtained (repo carries an MIT `LICENSE`)

## Final technical pass
- [ ] `pip install -r requirements.txt` succeeds on a clean environment
- [ ] `playwright install chromium` completed
- [ ] A live run completed end-to-end with your own Azure OpenAI / Foundry / ADO config
- [ ] Secret scan clean over the full git history (e.g. `git secrets` / GitHub push protection)
- [ ] No `__pycache__`, `output_data/`, recordings, or logs committed

## Submission split (recommended)
| Project | Challenge track | Microsoft IQ |
|---|---|---|
| AI Tester Agent | 🎨 Creative Apps (GitHub Copilot) | Foundry IQ |
| Agent Guild (multi-agent) | 🧠 Reasoning Agents (Microsoft Foundry) | Foundry IQ |

Both projects live in the **same public repository**; each submission links the same repo
and points to its respective entry mode (`--mode single` / `--mode collaborate`).
