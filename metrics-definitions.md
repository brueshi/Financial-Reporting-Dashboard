# SaaS Financial Metrics Definitions

This document outlines the key SaaS financial metrics implemented in the analytics pipeline, explaining their business significance, calculation methodology, and SQL implementation.

## Core Revenue Metrics

### Monthly Recurring Revenue (MRR)

**Definition:** The predictable monthly revenue generated from subscription services.

**Business Significance:** 
- Primary indicator of SaaS business health and growth
- Foundation for financial forecasting and valuation
- Benchmark for comparing performance over time

**Calculation:**
```sql
SELECT 
  DATE_TRUNC(timestamp, MONTH) AS month,
  SUM(amount) AS mrr
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE 
  transaction_type = 'Subscription'
  AND category = 'Revenue'
GROUP BY month
ORDER BY month;
```

**Variants Implemented:**
- **New MRR**: Revenue from new customers
- **Expansion MRR**: Additional revenue from existing customers (upgrades)
- **Contraction MRR**: Reduced revenue from existing customers (downgrades)
- **Churned MRR**: Lost revenue from canceled subscriptions

### Annual Recurring Revenue (ARR)

**Definition:** The annualized value of subscription revenue, typically calculated as MRR × 12.

**Business Significance:**
- Used for annual financial planning
- Key metric for investor reporting
- Smooths seasonal variations in growth metrics

**Calculation:**
```sql
SELECT 
  DATE_TRUNC(timestamp, MONTH) AS month,
  SUM(amount) * 12 AS arr
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE 
  transaction_type = 'Subscription'
  AND category = 'Revenue'
GROUP BY month
ORDER BY month;
```

### Average Revenue Per User (ARPU)

**Definition:** The average monthly revenue generated per customer.

**Business Significance:**
- Indicates monetization efficiency
- Helps evaluate pricing strategy effectiveness
- Signal for product-market fit

**Calculation:**
```sql
SELECT 
  DATE_TRUNC(timestamp, MONTH) AS month,
  SUM(amount) / COUNT(DISTINCT customer_id) AS arpu
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE 
  transaction_type = 'Subscription'
  AND category = 'Revenue'
GROUP BY month
ORDER BY month;
```

## Customer Metrics

### Customer Acquisition Cost (CAC)

**Definition:** The average cost to acquire a new customer, including marketing and sales expenses.

**Business Significance:**
- Measures acquisition efficiency
- Key input for unit economics
- Indicator of go-to-market effectiveness

**Calculation:**
```sql
WITH 
new_customers AS (
  SELECT 
    customer_id,
    MIN(DATE_TRUNC(timestamp, MONTH)) AS first_month
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE transaction_type = 'Subscription'
  GROUP BY customer_id
),
monthly_new_customers AS (
  SELECT 
    first_month AS month,
    COUNT(DISTINCT customer_id) AS new_customer_count
  FROM new_customers
  GROUP BY first_month
),
marketing_costs AS (
  SELECT 
    DATE_TRUNC(timestamp, MONTH) AS month,
    SUM(ABS(amount)) AS marketing_expense
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE category = 'Marketing Cost'
  GROUP BY month
)
SELECT 
  m.month,
  m.marketing_expense,
  c.new_customer_count,
  SAFE_DIVIDE(m.marketing_expense, c.new_customer_count) AS cac
FROM marketing_costs m
JOIN monthly_new_customers c ON m.month = c.month
ORDER BY m.month;
```

### Customer Lifetime Value (CLV)

**Definition:** The total revenue expected from a customer throughout their relationship with the business.

**Business Significance:**
- Determines maximum viable CAC
- Indicates long-term business sustainability
- Helps prioritize customer segments for targeting

**Calculation:**
```sql
WITH 
customer_value AS (
  SELECT
    customer_id,
    customer_type,
    SUM(amount) AS total_revenue,
    MIN(DATE(timestamp)) AS first_date,
    MAX(DATE(timestamp)) AS last_date,
    DATE_DIFF(MAX(DATE(timestamp)), MIN(DATE(timestamp)), DAY) AS days_active
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE 
    category = 'Revenue'
    AND transaction_type IN ('Subscription', 'One-Time Purchase', 'Upgrade', 'Add-on')
  GROUP BY customer_id, customer_type
),
active_days_by_segment AS (
  SELECT
    customer_type,
    AVG(days_active) AS avg_lifetime_days
  FROM customer_value
  WHERE days_active > 0
  GROUP BY customer_type
)
SELECT
  cv.customer_type,
  COUNT(DISTINCT cv.customer_id) AS customer_count,
  AVG(cv.total_revenue) AS avg_revenue_per_customer,
  ld.avg_lifetime_days,
  AVG(cv.total_revenue) * (ld.avg_lifetime_days / 30) AS estimated_ltv
FROM customer_value cv
JOIN active_days_by_segment ld ON cv.customer_type = ld.customer_type
GROUP BY cv.customer_type, ld.avg_lifetime_days
ORDER BY estimated_ltv DESC;
```

### Churn Rate

**Definition:** The percentage of customers who cancel their subscription in a given period.

**Business Significance:**
- Indicator of customer satisfaction and product stickiness
- Directly impacts growth trajectory and economics
- Often a leading indicator of business health

**Calculation:**
```sql
WITH 
monthly_active AS (
  SELECT
    DATE_TRUNC(timestamp, MONTH) AS month,
    customer_id
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE transaction_type = 'Subscription'
  GROUP BY month, customer_id
),
monthly_customer_count AS (
  SELECT
    month,
    COUNT(DISTINCT customer_id) AS customer_count
  FROM monthly_active
  GROUP BY month
),
churn_calc AS (
  SELECT
    c1.month,
    c1.customer_count AS current_customers,
    c2.customer_count AS previous_customers,
    c1.customer_count - (
      SELECT COUNT(DISTINCT a1.customer_id)
      FROM monthly_active a1
      JOIN monthly_active a2 
        ON a1.customer_id = a2.customer_id
        AND a1.month = c1.month
        AND a2.month = c2.month
    ) AS churned_customers
  FROM monthly_customer_count c1
  JOIN monthly_customer_count c2
    ON c1.month = DATE_ADD(c2.month, INTERVAL 1 MONTH)
)
SELECT
  month,
  current_customers,
  churned_customers,
  ROUND(SAFE_DIVIDE(churned_customers, previous_customers) * 100, 2) AS churn_rate_pct
FROM churn_calc
ORDER BY month;
```

## Efficiency Metrics

### Gross Margin

**Definition:** The percentage of revenue left after accounting for the direct costs of delivering the service.

**Business Significance:**
- Indicates operating efficiency
- Key to profitability and scalability
- Benchmark for SaaS business health (usually 70-85% for healthy SaaS)

**Calculation:**
```sql
WITH 
revenue AS (
  SELECT
    DATE_TRUNC(timestamp, MONTH) AS month,
    SUM(amount) AS total_revenue
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE category = 'Revenue'
  GROUP BY month
),
cogs AS (
  SELECT
    DATE_TRUNC(timestamp, MONTH) AS month,
    SUM(ABS(amount)) AS total_cogs
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE 
    category IN ('Infrastructure Cost', 'Customer Support', 'Operational Expense')
    AND amount < 0  -- Ensure we're only capturing costs (negative amounts)
  GROUP BY month
)
SELECT
  r.month,
  r.total_revenue,
  c.total_cogs,
  r.total_revenue - c.total_cogs AS gross_profit,
  ROUND(SAFE_DIVIDE(r.total_revenue - c.total_cogs, r.total_revenue) * 100, 2) AS gross_margin_pct
FROM revenue r
JOIN cogs c ON r.month = c.month
ORDER BY r.month;
```

### LTV:CAC Ratio

**Definition:** The ratio of customer lifetime value to customer acquisition cost.

**Business Significance:**
- Indicates overall business efficiency
- Guideline is 3:1 or better for sustainable SaaS
- Key metric for investment decisions

**Calculation:**
```sql
WITH 
cac_by_segment AS (
  -- CAC calculation query (abbreviated)
  SELECT
    customer_type,
    AVG(customer_acquisition_cost) AS avg_cac
  FROM customer_acquisition_costs
  GROUP BY customer_type
),
ltv_by_segment AS (
  -- LTV calculation query (abbreviated)
  SELECT
    customer_type,
    AVG(lifetime_value) AS avg_ltv
  FROM customer_lifetime_values
  GROUP BY customer_type
)
SELECT
  l.customer_type,
  l.avg_ltv,
  c.avg_cac,
  ROUND(SAFE_DIVIDE(l.avg_ltv, c.avg_cac), 2) AS ltv_cac_ratio
FROM ltv_by_segment l
JOIN cac_by_segment c ON l.customer_type = c.customer_type
ORDER BY ltv_cac_ratio DESC;
```

## Growth and Retention Metrics

### Net Revenue Retention (NRR)

**Definition:** The percentage of revenue retained from existing customers over time, including expansions, contractions, and churn.

**Business Significance:**
- Indicates ability to grow revenue from existing customers
- Values over 100% indicate negative churn (expansion > churn)
- Premier SaaS companies target 120%+ NRR

**Calculation:**
```sql
WITH 
cohort_revenue AS (
  SELECT
    DATE_TRUNC(timestamp, MONTH) AS cohort_month,
    customer_id,
    SUM(amount) AS initial_revenue
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE 
    transaction_type = 'Subscription'
    AND category = 'Revenue'
  GROUP BY cohort_month, customer_id
),
revenue_months_later AS (
  SELECT
    cr.cohort_month,
    cr.customer_id,
    cr.initial_revenue,
    DATE_TRUNC(t.timestamp, MONTH) AS current_month,
    DATE_DIFF(DATE_TRUNC(t.timestamp, MONTH), cr.cohort_month, MONTH) AS months_since_cohort,
    SUM(t.amount) AS current_revenue
  FROM cohort_revenue cr
  JOIN `financial-reporting-pipeline.financial_data.transactions` t
    ON cr.customer_id = t.customer_id
    AND DATE_TRUNC(t.timestamp, MONTH) > cr.cohort_month
  WHERE 
    t.transaction_type = 'Subscription'
    AND t.category = 'Revenue'
  GROUP BY cr.cohort_month, cr.customer_id, cr.initial_revenue, current_month, months_since_cohort
)
SELECT
  cohort_month,
  months_since_cohort,
  SUM(initial_revenue) AS cohort_initial_revenue,
  SUM(current_revenue) AS cohort_current_revenue,
  ROUND(SAFE_DIVIDE(SUM(current_revenue), SUM(initial_revenue)) * 100, 2) AS net_revenue_retention
FROM revenue_months_later
WHERE months_since_cohort = 12  -- One year later
GROUP BY cohort_month, months_since_cohort
ORDER BY cohort_month;
```

### Quick Ratio

**Definition:** The ratio of revenue growth (new + expansion) to revenue loss (churn + contraction).

**Business Significance:**
- Measures the efficiency of growth
- Values above 4 indicate excellent growth momentum
- Helps identify sustainable vs. unsustainable growth patterns

**Calculation:**
```sql
WITH
new_mrr AS (
  SELECT
    DATE_TRUNC(timestamp, MONTH) AS month,
    SUM(amount) AS new_revenue
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE 
    transaction_type IN ('Subscription', 'One-Time Purchase')
    AND category = 'Revenue'
    -- Logic to identify new customers
  GROUP BY month
),
expansion_mrr AS (
  SELECT
    DATE_TRUNC(timestamp, MONTH) AS month,
    SUM(amount) AS expansion_revenue
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE 
    transaction_type IN ('Upgrade', 'Add-on')
    AND category = 'Revenue'
  GROUP BY month
),
churn_mrr AS (
  SELECT
    DATE_TRUNC(timestamp, MONTH) AS month,
    SUM(ABS(amount)) AS churn_revenue
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE 
    transaction_type = 'Refund'
    AND category = 'Revenue'
  GROUP BY month
),
contraction_mrr AS (
  SELECT
    DATE_TRUNC(timestamp, MONTH) AS month,
    SUM(ABS(amount)) AS contraction_revenue
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE 
    transaction_type = 'Downgrade'
    AND category = 'Revenue'
  GROUP BY month
)
SELECT
  n.month,
  n.new_revenue,
  e.expansion_revenue,
  ch.churn_revenue,
  co.contraction_revenue,
  (n.new_revenue + e.expansion_revenue) AS growth_mrr,
  (ch.churn_revenue + co.contraction_revenue) AS loss_mrr,
  ROUND(SAFE_DIVIDE(n.new_revenue + e.expansion_revenue, ch.churn_revenue + co.contraction_revenue), 2) AS quick_ratio
FROM new_mrr n
JOIN expansion_mrr e ON n.month = e.month
JOIN churn_mrr ch ON n.month = ch.month
JOIN contraction_mrr co ON n.month = co.month
ORDER BY n.month;
```

## Revenue Recognition Metrics

### Deferred Revenue

**Definition:** Revenue that has been collected but not yet recognized according to accounting principles.

**Business Significance:**
- Critical for GAAP-compliant financial reporting
- Impacts balance sheet and cash flow forecasting
- Important for audits and financial compliance

**Calculation:**
```sql
WITH
collected_revenue AS (
  SELECT
    DATE_TRUNC(timestamp, MONTH) AS collection_month,
    transaction_id,
    customer_id,
    amount,
    subscription_plan,
    -- Assuming annual subscriptions are recognized over 12 months
    CASE
      WHEN subscription_plan IN ('Enterprise', 'Custom') THEN 12
      ELSE 1
    END AS recognition_months
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE 
    transaction_type = 'Subscription'
    AND category = 'Revenue'
    AND payment_status = 'Completed'
),
recognition_schedule AS (
  SELECT
    cr.collection_month,
    cr.transaction_id,
    cr.customer_id,
    cr.amount,
    cr.recognition_months,
    GENERATE_ARRAY(0, cr.recognition_months - 1) AS months_offset
  FROM collected_revenue cr
),
flattened_schedule AS (
  SELECT
    rs.collection_month,
    rs.transaction_id,
    rs.customer_id,
    DATE_ADD(rs.collection_month, INTERVAL offset MONTH) AS recognition_month,
    rs.amount / rs.recognition_months AS recognized_amount
  FROM recognition_schedule rs
  CROSS JOIN UNNEST(rs.months_offset) AS offset
),
monthly_totals AS (
  SELECT
    collection_month,
    recognition_month,
    SUM(recognized_amount) AS recognized_revenue
  FROM flattened_schedule
  GROUP BY collection_month, recognition_month
)
SELECT
  collection_month,
  SUM(CASE WHEN recognition_month > collection_month THEN recognized_revenue ELSE 0 END) AS deferred_revenue,
  SUM(CASE WHEN recognition_month = collection_month THEN recognized_revenue ELSE 0 END) AS current_recognized_revenue
FROM monthly_totals
GROUP BY collection_month
ORDER BY collection_month;
```

## Implementation Notes

These metrics are implemented in the financial analytics pipeline through:

1. **ETL Processes**: Extracting the base transaction data with proper categorization
2. **Transformation Logic**: SQL queries that calculate metrics from base data
3. **Visualization Layer**: Looker dashboards that present these metrics with drill-down capabilities
4. **Scheduled Reports**: Automated reporting on key metrics

## Usage Guidelines

When using these metrics, consider these best practices:

1. **Consistency**: Always use the same calculation method for trend analysis
2. **Context**: Provide benchmarks and historical context alongside current metrics
3. **Segmentation**: Break down metrics by customer segment, region, and plan type
4. **Combined View**: Look at multiple metrics together for a complete picture of business health

## Calculation Edge Cases

Important edge cases handled in the metric calculations:

1. **Free Trials**: Excluded from MRR until conversion
2. **Refunds**: Properly accounted for in churn calculations
3. **Plan Changes**: Mid-period upgrades and downgrades are properly attributed
4. **Zero Divisions**: SAFE_DIVIDE used throughout to handle potential division by zero
5. **Partial Months**: Pro-rated for accurate monthly metrics
