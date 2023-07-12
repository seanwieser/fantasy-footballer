CREATE TABLE IF NOT EXISTS public.players (
    player_id text PRIMARY KEY,

    name text,
    year text,
    pos_rank text,
    eligible_slots text[],
    acquisition_type text,
    pro_team text,
    on_team_id integer,
    position text,
    injury_status text,
    injured boolean,
    total_points decimal,
    projected_total_points decimal,
    percent_owned decimal,
    percent_started decimal,
    stats jsonb

);

CREATE TABLE public.players_stage (val jsonb);
COPY players_stage from '/player_data/players_2018.json.csv' csv quote e'\x01' delimiter e'\x02';
COPY players_stage from '/player_data/players_2019.json.csv' csv quote e'\x01' delimiter e'\x02';
COPY players_stage from '/player_data/players_2020.json.csv' csv quote e'\x01' delimiter e'\x02';
COPY players_stage from '/player_data/players_2021.json.csv' csv quote e'\x01' delimiter e'\x02';
COPY players_stage from '/player_data/players_2022.json.csv' csv quote e'\x01' delimiter e'\x02';


WITH players_stage_flat AS (
    select 
        replace(replace(replace(lower(val->>'name'), '.', ''), ' ', '_'), '''', '')  || '_' || cast(val->'year' as text)   as player_id,
        val->>'name'  as name,
        val->>'year' as year,
        cast(val->'posRank' as integer)             as pos_rank,
		string_to_array(replace(replace(left(right(val->>'eligibleSlots', -1), -1), ' ', ''), '"', ''), ',')::text[] as eligible_slots,
        val->'acquisitionType'             as acquisition_type,
        val->>'proTeam'              as pro_team,
        cast(val->'onTeamId' as integer)                           as on_team_id,
        val->>'position'          as position,
        val->>'injuryStatus'                  as injury_status,
        cast(val->>'injured' as boolean)             as injured,
        cast(val->'total_points' as decimal)                    as total_points,
        cast(val->'projected_total_points' as decimal)             as projected_total_points,
        cast(val->'percent_owned' as decimal)                      as percent_owned, 
        cast(val->'percent_started' as decimal) as percent_started,
        val->'stats' as stats
        from public.players_stage
)
INSERT INTO players select * from players_stage_flat;
