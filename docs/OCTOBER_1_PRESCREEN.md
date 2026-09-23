# October 1, 2026 — BoponX prescreening release plan
**Team EARTH.exe · Controlled demonstration · Status: in preparation**

The supplied Bangladesh participant guide describes a 240-second **concept-focused**
prescreening video on October 1. The local form and guide give conflicting cutoff
times. Until the Dhaka Local Lead confirms the authoritative time, complete and
submit on **September 30 (Bangladesh time), before the earlier stated cutoff**.
The October prescreening is not the final global hackathon submission.

## The single demonstration that must work

1. Show the BoponX animated CSS-3D agricultural hero and the public-domain Natural Earth Bangladesh atlas with a single *provisional Rajshahi pilot* pin. Explain that all 3D landscape elements are conceptual.
2. Show the **actual validated** Rajshahi regional 2024 NASA POWER snapshot.
3. Change monthly rainfall/temperature; select a month and read its source,
   coverage and units. The 3D rainfall columns represent *historical data*.
4. Open the NASA evidence drawer, source URL and raw snapshot identity.
5. Enter a pilot farm profile, choose a start month and priority, generate the working **three-month bilingual preparation brief**, and use the browser **Print / Save as PDF** option. Show the actual missing-input labels.
6. Explain that the report is a *field-monitoring and preparation routine*, not an agronomic crop calendar. Show how 2024 historical references remain separated from future months. Explain the **planned** three-season crop-rotation comparison and what still
   requires crop calendars, local soil constraints and direct NASA Earth-observation
   evidence. Do not show a fabricated recommendation.

If the dataset is unavailable on recording day, do not substitute synthetic
numbers. Use the independently validated, pinned local snapshot or state that the
data screen is unavailable. Show actual code and test output rather than mock API
responses.

## 240-second storyboard (record what actually works)

| Time | Screen / narrator focus |
| --- | --- |
| 00:00–00:15 | EARTH.exe, BoponX, Bangladesh, Field Shift challenge. |
| 00:15–00:50 | Farmer problem: rainfall variability, water constraints, soil knowledge gaps and crop-rotation choices. |
| 00:50–01:40 | Product interaction and Bangladesh-first bilingual UX; clarify conceptual 3D artwork is not a satellite map. |
| 01:40–02:45 | Live working app: NASA monthly data, 3D Bangladesh atlas and historical rainfall, farmer profile → three-month bilingual preparation brief → Print / Save as PDF. |
| 02:45–03:30 | Show provenance and source checks; distinguish 2024 MERRA-2 reanalysis from future forecasts and preparation checklists from pending crop-rotation calculations. |
| 03:30–03:50 | Next milestones: source-reviewed rotation rules and material direct NASA EO integration; show code and documented gates. |
| 03:50–04:00 | Closing: “From Space to Soil / মহাকাশ থেকে মাটিতে”; public repository, team identity. |

**Narration rule:** The current implementation is an environmental-evidence and
farm-intake prototype. Do **not** call it a deployed agronomic recommender, an
AI forecast, a yield optimizer, or a validated soil-health model. Use “proposed”
or “next milestone” for functionality that is not in the source code.

## Source and demo integrity

- Record the exact version/commit used. Keep the pinned raw NASA response and
  derived snapshot on the demo laptop. Run `python -m scripts.verify_pilot`.
- Show 2024 explicitly. A single year cannot establish a long-term climate trend or predict the weather in a chosen 2026–27 report month. The PDF must visibly say PREPARATION BRIEF — NOT A CROP PRESCRIPTION.
- The POWER pilot meteorological source returned **MERRA2 reanalysis**, not a
  direct satellite precipitation retrieval. Do not imply IMERG or SMAP is live.
- This is an **independent competition entry**. Do not add NASA or SpaceX
  endorsement wording. Cite NASA POWER as the environmental-data provider.
- Source-reviewed agronomic rules and local-soil input are release gates, not
  assumptions that the prototype has already validated.
- Credit any open data, imagery, music, graphics and AI-assisted work.
  Our app's CSS 3D visuals are original conceptual art.

## Submission fields — safe draft

**Project name:** BoponX  
**Team:** EARTH.exe  
**Challenge:** Field Shift: Adapting Farms with NASA Data  
**Global team URL:** [team lead must paste actual NASA global team URL]  
**NASA data source:** NASA POWER Daily API (T2M, PRECTOTCORR; 2024; Rajshahi
reference point; MERRA-2 reanalysis). Direct NASA Earth-observation product
under feasibility review, **not yet integrated**.

**Project description:**

> BoponX is a bilingual, mobile-first decision-support concept for exploring
> climate-resilient crop rotations. Our working prescreening prototype integrates
> real NASA POWER regional historical temperature and precipitation data with
> transparent monthly calculations, a source-evidence panel, and a farm profile
> that preserves unknown soil inputs. The proposed next stage combines these
> environmental indicators with locally reviewed crop calendars, soil constraints
> and farmer priorities in an explainable three-season comparison engine. The
> current prototype does not produce agricultural recommendations or forecasts.

**Public source URL:** https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026  
**240-second video URL:** [paste public video URL after uploading]  
**Live demo URL:** [paste only after deployment and anonymous testing]

## Freeze and release gates

Before recording: `pytest` green, `npm run build` green, pinned-data
verification green; climate API reports the expected snapshot; display checked
at 360px and 1366px; Bangla legible; reduced-motion preview checked. Test every
button with mouse and keyboard. Confirm source URLs open in a private window.

Before submitting: verify the **public video plays in a private browser**, the
repository is public, no secrets or unapproved agronomic data are committed,
title/credits/links are accurate, and the video meets the local form's exact
length/format instructions. Save the final upload confirmation and submission
time. The team lead should verify the current Local Lead instructions rather
than relying on an ambiguous guide timestamp.

After October 1: re-check the complete Field Shift statement when released,
review NASA-specified datasets, finalize agronomic evidence, implement and test
the rotation engine, and rebaseline the event-ready release.
