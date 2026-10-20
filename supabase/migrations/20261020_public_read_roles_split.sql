drop policy if exists "public can read reviewed evidence" on public.boponx_entries;
create policy "visitors can read reviewed evidence" on public.boponx_entries for select to anon using(review_state='approved');
create policy "editors can read all evidence" on public.boponx_entries for select to authenticated using(review_state='approved' or (select private.boponx_is_editor()));