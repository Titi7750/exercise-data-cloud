{{ config(materialized='table') }}

with commandes as (
    select * from {{ ref('stg_commandes') }}
),

clients as (
    select * from {{ ref('stg_clients') }}
)

select
    commandes.order_id,
    commandes.customer_id,
    clients.customer_unique_id,
    commandes.order_purchase_timestamp
from commandes
left join clients on commandes.customer_id = clients.customer_id
