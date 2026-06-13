"""Load test cases either from a local JSON file or from Azure DevOps."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from .config import azure_devops
from .pipeline import TestCase

logger = logging.getLogger(__name__)


def load_from_json(path: str | Path) -> list[TestCase]:
    """Load test cases from a JSON file.

    Expected shape:
        [{"feature": "...", "instructions": "...", "test_case_title": "..."}]
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = [
        TestCase(
            feature=item["feature"],
            instructions=item["instructions"],
            test_case_title=item.get("test_case_title"),
        )
        for item in data
    ]
    logger.info("Loaded %s test case(s) from %s.", len(cases), path)
    return cases


def load_from_ado(query_id: str | None = None) -> list[TestCase]:
    """Load test cases from a saved Azure DevOps query.

    Each matched work item becomes a TestCase using its title and its
    acceptance criteria / steps field as instructions.
    """
    from .azure_devops import AzureDevOpsClient

    query_id = query_id or azure_devops.test_query_id
    if not query_id:
        raise ValueError("No ADO query id provided (set ADO_TEST_QUERY_ID).")

    client = AzureDevOpsClient()
    ids = client.run_query(query_id)
    cases: list[TestCase] = []
    for wid in ids:
        wi = client.get_work_item(wid)
        fields = wi.get("fields", {})
        title = fields.get("System.Title", f"WorkItem {wid}")
        instructions = (
            fields.get("Microsoft.VSTS.Common.AcceptanceCriteria")
            or fields.get("Microsoft.VSTS.TCM.Steps")
            or fields.get("System.Description")
            or ""
        )
        cases.append(TestCase(feature=title, instructions=_strip_html(instructions),
                              test_case_title=title))
    logger.info("Loaded %s test case(s) from ADO query %s.", len(cases), query_id)
    return cases


def _strip_html(text: str) -> str:
    """Best-effort HTML -> text for ADO rich-text fields."""
    if not text:
        return ""
    try:
        from lxml import html

        return html.fromstring(text).text_content().strip()
    except Exception:
        import re

        return re.sub(r"<[^>]+>", " ", text).strip()
