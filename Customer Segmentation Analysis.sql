SELECT 
  customer_type,
  region,
  COUNT(DISTINCT customer_id) AS customer_count,
  SUM(amount) AS total_revenue,
  SUM(amount) / COUNT(DISTINCT customer_id) AS avg_revenue_per_customer
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE category = 'Revenue'
  AND transaction_type IN ('Subscription', 'One-Time Purchase', 'Upgrade', 'Add-on')
GROUP BY customer_type, region
ORDER BY total_revenue DESC;