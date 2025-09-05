{{ config(materialized='view') }}

select
    cast(order_id as string) as order_id,
    cast(customer_id as string) as customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date
from {{ source('raw_data', 'commandes') }}