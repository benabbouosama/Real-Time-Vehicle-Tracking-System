with raw_vehicle_data as (
    select * from {{ source('my_dataset', 'vehicle_data') }}
),

cleaned_vehicle_data as (
    select
        id,
        deviceId,
        timestamp,
        speed,
        direction,  
        make,
        model,
        year
    from raw_vehicle_data
    where speed > 0
)

select * from cleaned_vehicle_data
