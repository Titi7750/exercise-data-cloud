{{ config(materialized='view') }}

select
    cast(customer_id as string) as customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
from {{ source('raw_data', 'clients') }}