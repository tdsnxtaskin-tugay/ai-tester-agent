"""Minimal Azure DevOps REST client.

Only the surface this agent needs:
  * run a saved work-item query (to fetch the User Stories / Test Cases to test)
  * fetch work-item fields
  * create a Test Run, add results, and attach the recording
  * close the Test Run

Generic and configuration-driven — no organization-specific logic.
Docs: https://learn.microsoft.com/rest/api/azure/devops/
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Any

import requests

from .config import azure_devops

logger = logging.getLogger(__name__)

_API_VERSION = "7.1"


class AzureDevOpsClient:
    def __init__(self) -> None:
        self._cfg = azure_devops
        if not self._cfg.configured:
            raise RuntimeError(
                "Azure DevOps is not configured. Set ADO_ORGANIZATION, "
                "ADO_PROJECT and ADO_PERSONAL_ACCESS_TOKEN in your .env."
            )
        token = base64.b64encode(f":{self._cfg.pat}".encode()).decode()
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        })

    # -- internal helpers ---------------------------------------------------
    def _url(self, path: str) -> str:
        return f"{self._cfg.base_url}/{path}"

    def _get(self, path: str, **params: Any) -> dict:
        params.setdefault("api-version", _API_VERSION)
        resp = self._session.get(self._url(path), params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: Any, **params: Any) -> dict:
        params.setdefault("api-version", _API_VERSION)
        resp = self._session.post(self._url(path), json=payload, params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, path: str, payload: Any, **params: Any) -> dict:
        params.setdefault("api-version", _API_VERSION)
        resp = self._session.patch(self._url(path), json=payload, params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()

    # -- work items ---------------------------------------------------------
    def run_query(self, query_id: str) -> list[int]:
        """Run a saved query and return the matched work-item IDs."""
        data = self._get(f"wit/wiql/{query_id}")
        return [wi["id"] for wi in data.get("workItems", [])]

    def get_work_item(self, work_item_id: int) -> dict:
        return self._get(f"wit/workitems/{work_item_id}", expand="All")

    # -- test runs ----------------------------------------------------------
    def create_test_run(self, name: str, plan_id: int | None = None) -> int:
        payload: dict[str, Any] = {"name": name, "automated": True, "state": "InProgress"}
        if plan_id:
            payload["plan"] = {"id": str(plan_id)}
        run = self._post("test/runs", payload)
        run_id = run["id"]
        logger.info("Created Test Run %s (%s).", run_id, name)
        return run_id

    def add_test_result(self, run_id: int, *, test_case_title: str,
                        outcome: str, comment: str = "") -> int:
        """Add a single result to a run. outcome: 'Passed' | 'Failed'."""
        payload = [{
            "testCaseTitle": test_case_title,
            "automatedTestName": test_case_title,
            "outcome": outcome,
            "state": "Completed",
            "comment": comment,
        }]
        data = self._post(f"test/runs/{run_id}/results", payload)
        result_id = data["value"][0]["id"]
        logger.info("Added result %s to run %s: %s.", result_id, run_id, outcome)
        return result_id

    def attach_video_to_run(self, run_id: int, video_path: str,
                            comment: str = "Browser session recording") -> None:
        """Attach a recording to the Test Run."""
        if not os.path.exists(video_path):
            logger.warning("Video not found, skipping attachment: %s", video_path)
            return
        with open(video_path, "rb") as fh:
            encoded = base64.b64encode(fh.read()).decode()
        payload = {
            "stream": encoded,
            "fileName": os.path.basename(video_path),
            "comment": comment,
            "attachmentType": "GeneralAttachment",
        }
        self._post(f"test/runs/{run_id}/attachments", payload)
        logger.info("Attached %s to run %s.", os.path.basename(video_path), run_id)

    def complete_test_run(self, run_id: int) -> None:
        self._patch(f"test/runs/{run_id}", {"state": "Completed"})
        logger.info("Completed Test Run %s.", run_id)
