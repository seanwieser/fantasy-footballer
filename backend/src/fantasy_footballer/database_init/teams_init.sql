CREATE TABLE IF NOT EXISTS public.teams (
    team_id text PRIMARY KEY,

    team_abbrev text,
    year text,
    team_name text,
    division_id text,
    division_name text,
    wins  integer,
    losses  integer,
    ties  integer,
    points_for  decimal,
    points_against  decimal,
    acquisitions  integer,
    acquisition_budget_spent  integer,
    drops  integer,
    trades  integer,
    owner text,
    streak_type text,
    streak_length  integer,
    standing  integer,
    final_standing  integer,
    draft_projected_rank  integer,
    playoff_pct  integer,
    roster integer[],
    schedule jsonb[]
);

CREATE TABLE public.teams_stage (val jsonb);
COPY teams_stage from '/team_data/teams_2018.json.csv' csv quote e'\x01' delimiter e'\x02';
COPY teams_stage from '/team_data/teams_2020.json.csv' csv quote e'\x01' delimiter e'\x02';
COPY teams_stage from '/team_data/teams_2021.json.csv' csv quote e'\x01' delimiter e'\x02';
COPY teams_stage from '/team_data/teams_2022.json.csv' csv quote e'\x01' delimiter e'\x02';
COPY teams_stage from '/team_data/teams_2023.json.csv' csv quote e'\x01' delimiter e'\x02';


WITH stage_flat AS (
    select 
        md5(val->>'team_abbrev' || '_' || cast(val->'year' as text))   as team_id,
        lower(val->>'team_abbrev')      as team_abbrev,
        val->>'year'     as year,
        val->>'team_name'          as team_name,
        val->>'division_id'        as division_id,
        val->>'division_name'      as division_name,
        cast(val->'wins'                           as integer)   as wins,
        cast(val->'losses'                         as integer)   as losses,
        cast(val->'ties'                           as integer)   as ties,
        cast(val->'points_for'                     as decimal)   as points_for,
        cast(val->'points_against'                 as decimal)   as points_against,
        cast(val->'acquisitions'                   as integer)   as acquisitions,
        cast(val->'acquisition_budget_spent'       as integer)   as acquisition_budget_spent,
        cast(val->'drops'                          as integer)   as drops, 
        cast(val->'trades'                         as integer)   as trades,
        val->>'owner'               as owner,
        val->>'streak_type'         as streak_type,
        cast(val->'streak_length'                  as integer)   as streak_length,
        cast(val->'standing'                       as integer)   as standing,
        cast(val->'final_standing'                 as integer)   as final_standing,
        cast(val->'draft_projected_rank'           as integer)   as draft_projected_rank,
        cast(val->'playoff_pct'                    as integer)   as playoff_pct,
		string_to_array(replace(left(right(cast(val->'roster' as varchar), -1), -1), ' ', ''), ',')::integer[] as roster,
		string_to_array(right(left(replace(replace(cast(val->'schedule' as varchar), ' ', ''), '},{', '}|{'), -1), -1), '|')::jsonb[] as schedule
    from public.teams_stage
)
INSERT INTO teams select * from stage_flat;