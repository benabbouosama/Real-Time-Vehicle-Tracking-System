with raw_gps_data as (
    select * from {{ source('my_dataset', 'gps_data') }}
),

cleaned_gps_data as (
    select
        deviceId,
        timestamp,
        vehicleType,
        location  
    from raw_gps_data
)

select * from cleaned_gps_data
