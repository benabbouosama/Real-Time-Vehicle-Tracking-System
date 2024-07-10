with raw_weather_data as (
    select * from {{ source('my_dataset', 'weather_data') }}
),

cleaned_weather_data as (
    select
        deviceId,
        location,
        temperature,
        weatherCondition,
        timestamp,
        precipitation,
        humidity,
        windSpeed
    from raw_weather_data
    where temperature is not null
)

select * from cleaned_weather_data
