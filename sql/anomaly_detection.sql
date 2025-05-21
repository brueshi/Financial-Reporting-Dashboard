SELECT t.*, m.centroid_id
FROM `financial-reporting-pipeline.financial_data.transactions` t
JOIN ML.PREDICT(MODEL `financial-reporting-pipeline.financial_data.anomaly_model`, 
                (SELECT amount FROM `financial-reporting-pipeline.financial_data.transactions` WHERE payment_status = 'Failed')) m
ON t.amount = m.amount
WHERE m.centroid_id = 1;  -- Adjust based on anomaly cluster
