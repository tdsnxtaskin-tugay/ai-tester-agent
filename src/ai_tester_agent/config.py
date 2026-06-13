"""Central configuration — loads all settings from environment / .env.

No company-specific values are hard-coded here; everything comes from the
environment so the project is safe to publish. Copy .env.example to .env and
fill in your own values.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Project root is two levels up from this file: src/ai_tester_agent/config.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DOTENV = PROJECT_ROOT / ".env"

if _DOTENV.exists():
    load_dotenv(_DOTENV)
else:
    # Not fatal — values may come from real environment variables (e.g. CI).
    print(f"[INFO] No .env found at {_DOTENV}; using process environment variables.")

# browser-use hardening: never sync runs to any cloud, never emit telemetry.
os.environ.setdefault("BROWSER_USE_CLOUD_SYNC", "false")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class AzureOpenAISettings:
    api_key: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.endpoint)


@dataclass(frozen=True)
class FoundryIQSettings:
    enabled: bool = _bool("FOUNDRY_IQ_ENABLED", True)
    project_endpoint: str | None = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
    knowledge_source: str = os.getenv("FOUNDRY_KNOWLEDGE_SOURCE", "test-knowledge")

    @property
    def configured(self) -> bool:
        return self.enabled and bool(self.project_endpoint)


@dataclass(frozen=True)
class AzureDevOpsSettings:
    organization: str | None = os.getenv("ADO_ORGANIZATION")
    project: str | None = os.getenv("ADO_PROJECT")
    pat: str | None = os.getenv("ADO_PERSONAL_ACCESS_TOKEN")
    plan_id: int = _int("ADO_PLAN_ID", 0)
    test_query_id: str | None = os.getenv("ADO_TEST_QUERY_ID")

    @property
    def configured(self) -> bool:
        return bool(self.organization and self.project and self.pat)

    @property
    def base_url(self) -> str:
        return f"https://dev.azure.com/{self.organization}/{self.project}/_apis"


@dataclass(frozen=True)
class AgentSettings:
    max_steps: int = _int("AGENT_MAX_STEPS", 25)
    max_actions_per_step: int = _int("AGENT_MAX_ACTIONS_PER_STEP", 5)
    record_video: bool = _bool("AGENT_RECORD_VIDEO", True)
    headless: bool = _bool("AGENT_HEADLESS", True)
    target_base_url: str | None = os.getenv("TARGET_BASE_URL")


# Output locations (git-ignored)
OUTPUT_DIR = PROJECT_ROOT / "output_data"
RAW_RECORDING_DIR = OUTPUT_DIR / "raw_recordings"
PROCESSED_VIDEO_DIR = OUTPUT_DIR / "processed_video"
LOG_DIR = OUTPUT_DIR / "logs"

azure_openai = AzureOpenAISettings()
foundry_iq = FoundryIQSettings()
azure_devops = AzureDevOpsSettings()
agent = AgentSettings()


def ensure_output_dirs() -> None:
    for d in (RAW_RECORDING_DIR, PROCESSED_VIDEO_DIR, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)
