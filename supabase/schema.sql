create table if not exists public.daily_usage (
    scope text not null check (scope in ('user', 'global')),
    subject_hash text not null,
    usage_date date not null,
    comparisons integer not null default 0 check (comparisons >= 0),
    primary key (scope, subject_hash, usage_date)
);

alter table public.daily_usage enable row level security;
revoke all on public.daily_usage from public, anon, authenticated;
grant select, insert, update on public.daily_usage to service_role;

create or replace function public.reserve_daily_comparison(p_user_hash text)
returns table (
    allowed boolean,
    user_comparisons integer,
    user_remaining integer,
    global_comparisons integer,
    global_remaining integer,
    limit_reason text
)
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_date_utc date := timezone('utc', now())::date;
    user_count integer := 0;
    global_count integer := 0;
begin
    if p_user_hash is null or p_user_hash !~ '^[0-9a-f]{64}$' then
        raise exception 'Invalid account hash';
    end if;

    delete from public.daily_usage
     where usage_date < current_date_utc - 30;

    insert into public.daily_usage (scope, subject_hash, usage_date, comparisons)
    values ('global', 'global', current_date_utc, 0)
    on conflict (scope, subject_hash, usage_date) do nothing;

    select usage.comparisons
      into global_count
      from public.daily_usage as usage
     where usage.scope = 'global'
       and usage.subject_hash = 'global'
       and usage.usage_date = current_date_utc
     for update;

    if global_count >= 100 then
        select coalesce(max(usage.comparisons), 0)
          into user_count
          from public.daily_usage as usage
         where usage.scope = 'user'
           and usage.subject_hash = p_user_hash
           and usage.usage_date = current_date_utc;

        return query select
            false, user_count, greatest(20 - user_count, 0),
            global_count, 0, 'global'::text;
        return;
    end if;

    insert into public.daily_usage (scope, subject_hash, usage_date, comparisons)
    values ('user', p_user_hash, current_date_utc, 0)
    on conflict (scope, subject_hash, usage_date) do nothing;

    select usage.comparisons
      into user_count
      from public.daily_usage as usage
     where usage.scope = 'user'
       and usage.subject_hash = p_user_hash
       and usage.usage_date = current_date_utc
     for update;

    if user_count >= 20 then
        return query select
            false, user_count, 0, global_count, greatest(100 - global_count, 0),
            'user'::text;
        return;
    end if;

    update public.daily_usage as usage
       set comparisons = usage.comparisons + 1
     where usage.scope = 'user'
       and usage.subject_hash = p_user_hash
       and usage.usage_date = current_date_utc
    returning usage.comparisons into user_count;

    update public.daily_usage as usage
       set comparisons = usage.comparisons + 1
     where usage.scope = 'global'
       and usage.subject_hash = 'global'
       and usage.usage_date = current_date_utc
    returning usage.comparisons into global_count;

    return query select
        true, user_count, 20 - user_count, global_count, 100 - global_count,
        null::text;
end;
$$;

revoke all on function public.reserve_daily_comparison(text)
    from public, anon, authenticated;
grant execute on function public.reserve_daily_comparison(text) to service_role;
