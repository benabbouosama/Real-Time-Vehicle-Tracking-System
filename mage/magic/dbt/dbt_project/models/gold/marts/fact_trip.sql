with vehicle_data as (
    select * from {{ ref('stg_vehicle_data') }}
),

gps_data as (
    select * from {{ ref('stg_gps_data') }}
),

weather_data as (
    select * from {{ ref('stg_weather_data') }}
),

joined_data as (
    select
        v.id as vehicle_id,
        v.deviceId,
        v.timestamp as trip_timestamp,
        v.speed as vehicle_speed,
        v.direction as vehicle_direction,
        v.make as vehicle_make,
        v.model as vehicle_model,
        v.year as vehicle_year,
        g.location as gps_location,
        w.location as weather_location,
        w.temperature,
        w.weatherCondition,
        w.precipitation,
        w.humidity,
        w.windSpeed
    from vehicle_data v
    left join gps_data g on v.deviceId = g.deviceId and v.timestamp = g.timestamp
    left join weather_data w on v.deviceId = w.deviceId and v.timestamp = w.timestamp
)

select * from joined_data