SELECT DATE_TRUNC(timestamp, MONTH) as month, SUM(amount) as mrr
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE transaction_type = 'Subscription'
GROUP BY month;