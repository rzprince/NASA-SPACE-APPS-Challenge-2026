# BoponX interface quality and accessibility review
**Preview build · CSS-3D + React · Review status: automated build tested, field UX pending**

The quality target is **fast, legible, trustworthy farmer interaction**, not
a large source-code count or heavy effects. CSS-3D is decorative; real
information must remain accessible through text, controls, charts and tables.

## Human QA matrix — check before recording the demo

| View or interaction | Acceptance evidence | Status |
| --- | --- | --- |
| Desktop 1366×768 and 1920×1080 | No clipped hero headline, controls, orbit caption, chart axes or planning-card heading | Manual review required |
| Mobile 360×800 and 390×844 | Bangla labels legible without zoom; no horizontal scrolling or overlapped buttons | Manual review required |
| Tablet 768×1024 | Farm controls remain usable and card columns reflow | Manual review required |
| Language | Core farmer-facing English text has Bangla beside or beneath; no muted 10px-only Bengali action text | Manual review required |
| Keyboard | Links, input fields, monthly variable buttons, month picker and evidence/table disclosures all usable with Tab, Enter and Space | Manual review required |
| Reduced motion | OS `prefers-reduced-motion: reduce` disables continuous orbital/field animations without hiding information | CSS implemented; manual check required |
| Contrast | Text and form borders legible outdoors; check against WCAG 2.2 AA contrast targets where practical | Manual check required |
| API errors | Missing NASA data is clearly stated; never display placeholder numbers as measurements | Implemented; test in browser |
| Scientific chart | °C and mm identified; axes labelled; selected month and data coverage evident; incomplete month shows unavailable | Implemented; manual check |
| 3D integrity | Scene explicitly conceptual; Natural Earth 110m Bangladesh outline visibly identifies provisional pilot; stylized rivers are not actual hydrography; 3D rainfall columns use actual historical totals | Implemented; verify narrator script |
| Performance | No continuous WebGL; animations run in CSS; no third-party runtime artwork or remote font requirement | Review production build on mid-range Android |
| Data provenance | Raw SHA and original POWER source visible; only approved snapshot is shown | Implemented; run pinned integrity script |
| Report / PDF | Farm submission yields three planned months, actual 2024 historical reference year, bilingual missing inputs and checklist; Print / Save as PDF prints all pages without clipping, including Bengali on Samsung Internet and desktop Chrome | Automated API tests; manual print review required |
| Farmer testing | Ask at least one Bangla-speaking non-developer to complete the farm intake on a phone without guidance | Not yet completed |

## Development quality gates

```powershell
.\.venv\Scripts\python.exe -m pytest -q backend\tests
.\.venv\Scripts\python.exe -m scripts.verify_pilot
cd frontend
npm.cmd run build
```

A green CI build confirms compilation/tests—not scientific validity, visual
perfection, accessibility certification or competition outcome. Record manual
QA findings as GitHub issues. Do not describe untested features as completed.
