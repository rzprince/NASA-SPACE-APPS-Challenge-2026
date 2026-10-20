# BoponX secure administrator setup

## Project

Supabase: https://supabase.com/dashboard/project/ebkywbefthblevebnscc

Vercel: both services in the same Git-linked project, using vercel.toml.

## Role bootstrap (once)

1. In the deployed BoponX interface open **Admin** and choose **Request an editor account**.
2. Enter your own real email and strong password; confirm email if Supabase requests it.
3. In the Supabase SQL editor, an already authorized project owner runs **only after checking the email is correct**:

```sql
insert into public.boponx_admins(user_id, role, display_name)
select id, 'owner', 'Project owner'
from auth.users where lower(email)=lower('REPLACE_WITH_YOUR_CONFIRMED_EMAIL')
on conflict (user_id) do update set role='owner';
```

No account becomes an editor just by registering. Never put a service-role/secret key in Vite, the browser, a public GitHub file, or screenshots.

## Frontend configuration

Set VITE_BOPONX_SUPABASE_URL and VITE_BOPONX_SUPABASE_PUBLISHABLE_KEY for the Vercel **build**. Locally, add these variables to frontend/.env.local. Only public publishable keys belong in this file. This URL and key may be embedded in browser JavaScript; the data are protected by Supabase row-level security.

## Backend configuration

Set BOPONX_SUPABASE_URL and BOPONX_SUPABASE_PUBLISHABLE_KEY on the deployed API service. These read only approved plan_action records through the public RLS policy. The API uses no admin or service-role key.

## Admin functions

- Sign in / sign out / request account
- Search, filter, and inspect all content categories
- Create a record; verify the returned database row
- Update the selected record; verify returned database row
- Delete with an explicit confirmation; verify one deleted row
- Mark draft, approved, or archived
- See the last 80 audit events
- Enter bilingual titles, plain-language descriptions, URLs and structured JSON

## Editorial protocol

All generic crop calendars, simplified soil classes, and region risks from Earth.exe were seeded as **draft**. Review each claim against SRDI, BARC, BRRI, BAMIS and a qualified local agronomy expert, then approve for public display. A district label alone does not validate district soil, forecast or crop suitability. 

Only approved plan_action entries with `content.action_type="verification_only"` and `content.month_offset` of 0, 1 or 2 can be appended to an existing 90-day plan. Crop suitability or rotation ranking is never inferred from generic CMS content.

## QA checklist (must test with actual authorized admin)

1. Visit farmer guide signed out: only approved records show.
2. Sign in as admin: draft and archived records become visible in the editor.
3. Create unique test record, verify read and audit INSERT.
4. Edit title and status, verify persistence and audit UPDATE.
5. Refresh the browser, confirm saved values are retained.
6. Delete test record with confirmation, verify it disappears and audit DELETE exists.
7. Log out, confirm edits are no longer possible.
8. Test failed login and non-admin login are denied.
9. On mobile, check large controls, text wrapping and the browser's Bangla speech capability.
10. Verify /api/v1/health and /api/v1/plans/preview on the deployed URL; note when NASA upstream data are unavailable.

## No promise of coverage

The document does not contain a complete 90-day prescription model or per-field validated soil measurements. The source catalog is review-gated and the NASA POWER historical record is not a weather forecast.
