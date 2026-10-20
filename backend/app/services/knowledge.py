"""Attach published editorial verification tasks to BoponX's deterministic 90-day plan.

This reads only public, Supabase-RLS-approved records using a publishable key.
Database content cannot override NASA readings, farmer facts or agronomic evidence gates.
"""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Any

MAX_DB_TASKS = 24


def published_plan_tasks() -> list[dict[str, Any]]:
    base = os.getenv("BOPONX_SUPABASE_URL", "").rstrip("/")
    key = os.getenv("BOPONX_SUPABASE_PUBLISHABLE_KEY", "")
    if not (base.startswith("https://") and key):
        return []
    params = urlencode({
        "select": "code,title_en,title_bn,summary_en,summary_bn,region_code,source_name,source_url,content",
        "review_state": "eq.approved",
        "category": "eq.plan_action",
        "limit": str(MAX_DB_TASKS),
        "order": "code.asc",
    })
    request = Request(base + "/rest/v1/boponx_entries?" + params, headers={
        "apikey": key, "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=4.0) as response:
            payload = json.load(response)
        return payload if isinstance(payload, list) else []
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, TypeError):
        return []


def attach_reviewed_knowledge(plan: dict[str, Any], *, lookup=published_plan_tasks) -> dict[str, Any]:
    """Add published action references without altering the scientific model's verdict.

    Only tasks explicitly categorized as verification checks are admitted.
    Future task types need an independently reviewed mapping before activation.
    """
    registry = {
        "provider": "Supabase evidence CMS",
        "status": "unavailable_or_no_approved_actions",
        "tasks_appended": 0,
        "boundary": "Editorial checklist only. No crop suitability or forecast is inferred.",
    }
    plan["knowledge_registry"] = registry
    months = plan.get("months")
    if not isinstance(months, list):
        return plan
    region = str(plan.get("location", {}).get("region_id", "")).lower()
    added = 0
    for entry in lookup():
        if not isinstance(entry, dict):
            continue
        content = entry.get("content")
        if not isinstance(content, dict) or content.get("action_type") != "verification_only":
            continue
        offset = content.get("month_offset")
        if not isinstance(offset, int) or isinstance(offset, bool) or not 0 <= offset < min(len(months), 3):
            continue
        area = str(entry.get("region_code") or "").lower()
        if area and area != region:
            continue
        stage = months[offset]
        tasks = stage.get("tasks") if isinstance(stage, dict) else None
        if not isinstance(tasks, list):
            continue
        code = str(entry.get("code") or "")
        if not code or any(task.get("code") == code for task in tasks if isinstance(task, dict)):
            continue
        title_en = str(entry.get("title_en") or "").strip()
        title_bn = str(entry.get("title_bn") or "").strip()
        if not title_en or not title_bn:
            continue
        tasks.append({
            "code": code,
            "en": title_en + (". " + str(entry["summary_en"]) if entry.get("summary_en") else ""),
            "bn": title_bn + ("। " + str(entry["summary_bn"]) if entry.get("summary_bn") else ""),
            "category": "local_evidence_check",
            "reason": "Editorially published verification checklist; not a crop prescription.",
            "evidence": str(entry.get("source_url") or entry.get("source_name") or ""),
        })
        added += 1
    registry["status"] = "published_checklist_available" if added else "unavailable_or_no_approved_actions"
    registry["tasks_appended"] = added
    return plan
