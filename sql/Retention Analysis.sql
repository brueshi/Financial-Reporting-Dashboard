WITH first_purchase AS (
  SELECT 
    customer_id,
    MIN(DATE(timestamp)) AS first_month_date
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE transaction_type = 'Subscription'
  GROUP BY customer_id
),
active_months AS (
  SELECT 
    customer_id,
    DATE(timestamp) AS active_month_date
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE transaction_type = 'Subscription'
  GROUP BY customer_id, active_month_date
),
cohort_data AS (
  SELECT
    fp.first_month_date,
    fp.customer_id,
    am.active_month_date,
    DATE_DIFF(am.active_month_date, fp.first_month_date, MONTH) AS months_since_first
  FROM first_purchase fp
  JOIN active_months am ON fp.customer_id = am.customer_id
)
SELECT
  FORMAT_DATE('%Y-%m', first_month_date) AS cohort_month,
  months_since_first,
  COUNT(DISTINCT customer_id) AS active_customers,
  FIRST_VALUE(COUNT(DISTINCT customer_id)) OVER (
    PARTITION BY first_month_date 
    ORDER BY months_since_first
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) AS cohort_size,
  ROUND(
    COUNT(DISTINCT customer_id) * 100.0 / 
    FIRST_VALUE(COUNT(DISTINCT customer_id)) OVER (
      PARTITION BY first_month_date 
      ORDER BY months_since_first
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ), 2) AS retention_rate
FROM cohort_data
WHERE months_since_first BETWEEN 0 AND 12
GROUP BY cohort_month, first_month_date, months_since_first
ORDER BY first_month_date, months_since_first;
