"""LLM client factories.

Two clients are used:
  * `build_browser_llm()` -> browser-use ChatAzureOpenAI, drives the browser agent.
  * `build_chat_client()` -> plain Azure OpenAI client, used for result matching.
"""
from __future__ import annotations

import logging

from openai import AzureOpenAI

from .config import azure_openai

logger = logging.getLogger(__name__)


def build_browser_llm():
    """Create the ChatAzureOpenAI model that browser-use drives the browser with."""
    if not azure_openai.configured:
        raise RuntimeError(
            "Azure OpenAI is not configured. Set AZURE_OPENAI_API_KEY and "
            "AZURE_OPENAI_ENDPOINT in your .env."
        )

    # Imported lazily so the package can be imported without browser-use present.
    from browser_use import ChatAzureOpenAI

    llm = ChatAzureOpenAI(
        model=azure_openai.deployment,
        api_key=azure_openai.api_key,
        azure_endpoint=azure_openai.endpoint,
    )
    logger.info("Browser LLM initialized (deployment=%s).", azure_openai.deployment)
    return llm


def build_chat_client() -> AzureOpenAI:
    """Create a plain Azure OpenAI client for result-matching / reasoning calls."""
    if not azure_openai.configured:
        raise RuntimeError(
            "Azure OpenAI is not configured. Set AZURE_OPENAI_API_KEY and "
            "AZURE_OPENAI_ENDPOINT in your .env."
        )
    return AzureOpenAI(
        api_key=azure_openai.api_key,
        azure_endpoint=azure_openai.endpoint,
        api_version=azure_openai.api_version,
    )
