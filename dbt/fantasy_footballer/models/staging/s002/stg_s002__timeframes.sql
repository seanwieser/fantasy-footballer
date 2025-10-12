with source as (
    select *
    from {{ source('raw', 'timeframes') }}
),

renamed as (
    select
        -- identifiers
        season as season_year,
        season_type as season_type_id,
        week as week_number,

        -- season type descriptions
        case season_type
            when 1 then 'Regular Season'
            when 2 then 'Preseason'
            when 3 then 'Postseason'
            when 4 then 'Offseason'
            when 5 then 'Pro Bowl'
            else 'Unknown'
        end as season_type_name,

        -- timeframe names
        name as timeframe_name,
        short_name as timeframe_short_name,

        -- date fields
        cast(start_date as timestamp) as start_timestamp,
        cast(end_date as timestamp) as end_timestamp,
        cast(start_date as date) as start_date,
        cast(end_date as date) as end_date,

        -- API identifiers
        api_season,
        api_week,

        -- derived fields
        datediff('day', cast(start_date as timestamp), cast(end_date as timestamp)) + 1 as duration_days,

        -- metadata
        current_timestamp as _loaded_at

    from source
)

select * from renamed