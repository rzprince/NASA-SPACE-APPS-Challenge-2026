-- BoponX evidence registry and protected editorial CMS.
-- Source: Earth.exe (2026-10-20), NASA POWER and official Bangladesh authority references.
create extension if not exists pgcrypto;
create schema if not exists private;
create table if not exists public.boponx_admins (
 user_id uuid primary key references auth.users(id) on delete cascade,
 role text not null default 'editor' check(role in ('owner','editor')),
 display_name text not null default '',
 created_at timestamptz not null default now()
);
create table if not exists public.boponx_entries (
 id uuid primary key default gen_random_uuid(),
 category text not null check(category in ('district','region','season','soil','crop','hazard','source','plan_action')),
 code text not null check(code ~ '^[a-z0-9][a-z0-9_-]{1,89}$'),
 title_en text not null check(length(trim(title_en)) between 2 and 160),
 title_bn text not null default '',
 summary_en text not null default '',
 summary_bn text not null default '',
 region_code text not null default '',
 crop_code text not null default '',
 source_name text not null default '',
 source_url text not null default '' check(source_url='' or source_url ~ '^https://'),
 content jsonb not null default '{}'::jsonb check(jsonb_typeof(content)='object'),
 review_state text not null default 'draft' check(review_state in ('draft','approved','archived')),
 reviewed_at timestamptz,
 created_by uuid references auth.users(id) on delete set null,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique(category,code)
);
create index if not exists boponx_entries_category_review_idx on public.boponx_entries(category,review_state);
create index if not exists boponx_entries_region_idx on public.boponx_entries(region_code,category);
create table if not exists public.boponx_audit (
 id bigint generated always as identity primary key,
 entry_id uuid,
 action text not null,
 actor_id uuid,
 changed_at timestamptz not null default now(),
 before_data jsonb,
 after_data jsonb
);
create or replace function private.boponx_is_editor()
returns boolean language sql stable security definer set search_path=''
as $$select exists(select 1 from public.boponx_admins a where a.user_id=(select auth.uid()) and a.role in ('owner','editor'))$$;
revoke all on function private.boponx_is_editor() from public;
grant usage on schema private to authenticated;
grant execute on function private.boponx_is_editor() to authenticated;
create or replace function private.boponx_touch_entry()
returns trigger language plpgsql set search_path='' as $$
begin new.updated_at=now();
 if new.review_state='approved' and (tg_op='INSERT' or old.review_state is distinct from new.review_state) then new.reviewed_at=now(); end if;
 if new.review_state<>'approved' then new.reviewed_at=null; end if;
 return new; end $$;
drop trigger if exists boponx_touch_entry on public.boponx_entries;
create trigger boponx_touch_entry before insert or update on public.boponx_entries for each row execute function private.boponx_touch_entry();
create or replace function private.boponx_audit_entry()
returns trigger language plpgsql security definer set search_path='' as $$
begin
 insert into public.boponx_audit(entry_id,action,actor_id,before_data,after_data)
 values(coalesce(new.id,old.id),tg_op,auth.uid(),
 case when tg_op='INSERT' then null else to_jsonb(old) end,
 case when tg_op='DELETE' then null else to_jsonb(new) end);
 return coalesce(new,old);
end $$;
drop trigger if exists boponx_audit_entry on public.boponx_entries;
create trigger boponx_audit_entry after insert or update or delete on public.boponx_entries for each row execute function private.boponx_audit_entry();
alter table public.boponx_admins enable row level security;
alter table public.boponx_entries enable row level security;
alter table public.boponx_audit enable row level security;
revoke all on table public.boponx_admins,public.boponx_entries,public.boponx_audit from anon,authenticated;
grant select on public.boponx_entries to anon;
grant select,insert,update,delete on public.boponx_entries to authenticated;
grant select on public.boponx_admins,public.boponx_audit to authenticated;
grant usage,select on sequence public.boponx_audit_id_seq to authenticated;
drop policy if exists "admins can read their membership" on public.boponx_admins;
create policy "admins can read their membership" on public.boponx_admins for select to authenticated using(user_id=(select auth.uid()));
drop policy if exists "public can read reviewed evidence" on public.boponx_entries;
create policy "public can read reviewed evidence" on public.boponx_entries for select to anon,authenticated using(review_state='approved' or (select private.boponx_is_editor()));
drop policy if exists "editors can add evidence" on public.boponx_entries;
create policy "editors can add evidence" on public.boponx_entries for insert to authenticated with check((select private.boponx_is_editor()));
drop policy if exists "editors can revise evidence" on public.boponx_entries;
create policy "editors can revise evidence" on public.boponx_entries for update to authenticated using((select private.boponx_is_editor())) with check((select private.boponx_is_editor()));
drop policy if exists "editors can remove evidence" on public.boponx_entries;
create policy "editors can remove evidence" on public.boponx_entries for delete to authenticated using((select private.boponx_is_editor()));
drop policy if exists "editors read audit" on public.boponx_audit;
create policy "editors read audit" on public.boponx_audit for select to authenticated using((select private.boponx_is_editor()));
-- Deliberately no client-side insert/update/delete permissions on admin memberships or audit trail.
