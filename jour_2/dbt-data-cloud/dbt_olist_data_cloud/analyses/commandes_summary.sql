select
    count(distinct order_id) as nb_commandes,
    count(distinct customer_id) as nb_clients,
    round(safe_divide(count(distinct order_id), count(distinct customer_id)), 2) as commandes_par_client,
    min(order_purchase_timestamp) as date_premiere_commande,
    max(order_purchase_timestamp) as date_derniere_commande
from {{ ref('int_commandes_clients') }}
