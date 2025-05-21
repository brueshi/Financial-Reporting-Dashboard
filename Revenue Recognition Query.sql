SELECT 
  DATE_TRUNC(timestamp, MONTH) AS recognition_month,
  subscription_plan,
  SUM(CASE 
      WHEN transaction_type = 'Subscription' THEN amount
      WHEN transaction_type = 'Refund' THEN amount
      ELSE 0 
  END) AS recognized_revenue
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE category = 'Revenue'
GROUP BY recognition_month, subscription_plan
ORDER BY recognition_month, subscription_plan;