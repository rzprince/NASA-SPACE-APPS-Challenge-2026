"""The public evidence registry cannot write crop rankings or mutate NASA data."""
from copy import deepcopy

from backend.app.services.knowledge import attach_reviewed_knowledge


def _plan():
    return {
        "location": {"region_id": "rajshahi"},
        "decision_advice": {"verdict": "Evidence gate remains in place"},
        "months": [{"tasks": []} for _ in range(3)],
    }


def test_only_published_verification_entries_are_appended():
    original = _plan()
    entries = [
        {"code": "good", "title_en": "Verify with officer", "title_bn": "কৃষি অফিসে যাচাই করুন",
         "summary_en": "No crop is prescribed.", "content": {"month_offset": 1, "action_type": "verification_only"},
         "source_url": "https://apps.barc.gov.bd/cropzoning/"},
        {"code": "unsafe", "title_en": "Guaranteed yield", "title_bn": "নিশ্চিত ফলন",
         "content": {"month_offset": 0, "action_type": "crop_prescription"}},
        {"code": "wrong-region", "title_en": "Coastal note", "title_bn": "উপকূল",
         "region_code": "coast", "content": {"month_offset": 0, "action_type": "verification_only"}},
        {"code": "out-of-range", "title_en": "Future", "title_bn": "ভবিষ্যৎ",
         "content": {"month_offset": 3, "action_type": "verification_only"}},
        {"code": "missing-bangla", "title_en": "No translation", "title_bn": "",
         "content": {"month_offset": 0, "action_type": "verification_only"}},
    ]
    resulting = attach_reviewed_knowledge(deepcopy(original), lookup=lambda: entries)
    assert [len(month["tasks"]) for month in resulting["months"]] == [0, 1, 0]
    assert resulting["months"][1]["tasks"][0]["code"] == "good"
    assert resulting["months"][1]["tasks"][0]["bn"].startswith("কৃষি অফিসে")
    assert resulting["decision_advice"] == original["decision_advice"]
    assert resulting["knowledge_registry"]["tasks_appended"] == 1


def test_unconfigured_or_offline_registry_leaves_existing_plan_intact():
    original = _plan()
    original["months"][0]["tasks"].append({"code": "existing", "en": "Keep this"})
    result = attach_reviewed_knowledge(deepcopy(original), lookup=lambda: [])
    assert result["months"] == original["months"]
    assert result["knowledge_registry"]["status"] == "unavailable_or_no_approved_actions"


def test_duplicate_task_code_does_not_repeat():
    original = _plan()
    original["months"][0]["tasks"].append({"code": "a", "en": "Already here"})
    entry = {"code": "a", "title_en": "Again", "title_bn": "আবার", "content": {"month_offset": 0, "action_type": "verification_only"}}
    result = attach_reviewed_knowledge(original, lookup=lambda: [entry])
    assert len(result["months"][0]["tasks"]) == 1
