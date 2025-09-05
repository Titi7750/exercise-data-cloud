select
    count(distinct order_id) as nb_commandes,
    count(distinct customer_id) as nb_clients,
    round(safe_divide(count(distinct order_id), count(distinct customer_id)), 2) as commandes_par_client,
    min(order_purchase_timestamp) as date_premiere_commande,
    max(order_purchase_timestamp) as date_derniere_commande
from {{ ref('int_commandes_clients') }}

WITH cmd_par_client AS (
  SELECT
    customer_id,
    COUNT(DISTINCT order_id) AS nb_cmd
  FROM {{ ref('int_commandes_clients') }}
  GROUP BY 1
)
SELECT
  COUNT(*) AS total_clients,
  COUNTIF(nb_cmd >= 2) AS clients_recurrents
FROM cmd_par_client;
