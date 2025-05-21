# Data Dictionary: SaaS Financial Analytics

## Overview

This data dictionary documents the structure, fields, and semantic meaning of the data in the SaaS Financial Analytics pipeline. It serves as the central reference for all stakeholders working with the financial data, including finance teams, data analysts, and executives.

## Core Table: `transactions`

The primary fact table containing all financial transactions and events.

| Field Name | Data Type | Required | Description | Valid Values | Example Values |
|------------|-----------|----------|-------------|--------------|----------------|
| transaction_id | STRING | Yes | Unique identifier for each transaction record | Format: Prefix_UUID (REV_ for revenue, EXP_ for expenses) | REV_7A9B2C3D4E5F |
| timestamp | TIMESTAMP | Yes | Date and time when the transaction occurred | ISO-8601 format | 2023-05-15T14:23:45 |
| customer_id | STRING | Yes | Unique identifier linking to the customer | Format: CUST_########### | CUST_000012345 |
| amount | FLOAT | Yes | Monetary value of the transaction | Positive for revenue, negative for expenses | 99.99, -250.00 |
| transaction_type | STRING | Yes | Categorizes the nature of the transaction | 'Subscription', 'Refund', 'One-Time Purchase', 'Upgrade', 'Downgrade', 'Add-on' | Subscription |
| subscription_plan | STRING | No | The SaaS plan associated with the transaction | 'Free', 'Basic', 'Pro', 'Enterprise', 'Custom' | Pro |
| category | STRING | Yes | Financial classification for accounting purposes | 'Revenue', 'Marketing Cost', 'Operational Expense', 'Infrastructure Cost', 'Customer Support', 'R&D', 'Administrative' | Revenue |
| region | STRING | No | Geographic region of the customer | 'US', 'EU', 'APAC', 'LATAM', 'MEA' | EU |
| payment_status | STRING | Yes | Status of the payment transaction | 'Completed', 'Pending', 'Failed', 'Refunded', 'Disputed' | Completed |
| customer_type | STRING | No | Business segment of the customer | 'B2C', 'SMB', 'Mid-Market', 'Enterprise' | SMB |

## Derived Table: `monthly_metrics`

Aggregated monthly metrics table created from the transactions fact table.

| Field Name | Data Type | Description | Calculation Logic | Example Values |
|------------|-----------|-------------|-------------------|----------------|
| month | DATE | First day of the month for grouping | DATE_TRUNC(timestamp, MONTH) | 2023-05-01 |
| mrr | FLOAT | Monthly Recurring Revenue | SUM(amount) WHERE transaction_type = 'Subscription' | 45780.25 |
| active_customers | INTEGER | Count of customers with active subscriptions | COUNT(DISTINCT customer_id) WHERE transaction_type = 'Subscription' | 1250 |

## Derived Table: `cohort_retention`

Customer retention analysis by acquisition cohort.

| Field Name | Data Type | Description | Calculation Logic | Example Values |
|------------|-----------|-------------|-------------------|----------------|
| cohort_month | DATE | Month when customers were first acquired | MIN(DATE_TRUNC(timestamp, MONTH)) GROUP BY customer_id | 2023-01-01 |
| months_since_first | INTEGER | Number of months since customer acquisition | DATE_DIFF(current_month, cohort_month, MONTH) | 3 |
| cohort_size | INTEGER | Original number of customers in the cohort | COUNT(DISTINCT customer_id) | 435 |
| active_customers | INTEGER | Customers still active after X months | COUNT(DISTINCT customer_id) WHERE still active | 389 |
| retention_rate | FLOAT | Percentage of cohort still active | active_customers / cohort_size * 100 | 89.43 |

## Derived Table: `customer_segments`

Analysis of customers by segment and region.

| Field Name | Data Type | Description | Calculation Logic | Example Values |
|------------|-----------|-------------|-------------------|----------------|
| customer_type | STRING | Business segment | From transactions.customer_type | SMB |
| region | STRING | Geographic region | From transactions.region | EU |
| customer_count | INTEGER | Count of unique customers | COUNT(DISTINCT customer_id) | 780 |
| total_revenue | FLOAT | Total revenue from segment | SUM(amount) WHERE category = 'Revenue' | 125000.00 |
| avg_revenue_per_customer | FLOAT | Average revenue per customer | total_revenue / customer_count | 160.26 |

## Field Details

### `transaction_id`

- **Business Purpose**: Provides a unique identifier for each financial transaction for auditing and tracking.
- **Source**: Auto-generated during transaction creation.
- **Valid Format**: Prefix_UUID where prefix indicates transaction category.
- **Validation Rules**: Must be unique across all transactions and never null.
- **Notes**: Can be used to join with other systems (e.g., payment processor transactions).

### `timestamp`

- **Business Purpose**: Records when the transaction occurred for time-based analysis and reporting.
- **Source**: System-generated at transaction time.
- **Format**: ISO-8601 formatted datetime.
- **Time Zone**: UTC.
- **Validation Rules**: Cannot be in the future, must not be null.
- **Notes**: Used for partitioning in BigQuery for query optimization.

### `amount`

- **Business Purpose**: Records the monetary value of the transaction.
- **Source**: Calculated from product pricing or entered expense amount.
- **Format**: Decimal number with up to 2 decimal places.
- **Units**: USD (US Dollars).
- **Sign Convention**: Positive values represent incoming funds (revenue), negative values represent outgoing funds (expenses).
- **Validation Rules**: Must not be null, must not be zero.
- **Notes**: For multi-currency support in the future, will need to add currency code field.

### `transaction_type`

- **Business Purpose**: Categorizes the transaction for analysis and accounting purposes.
- **Source**: Assigned based on the nature of the financial event.
- **Valid Values**:
  - `Subscription`: Recurring subscription payment
  - `Refund`: Return of funds to customer
  - `One-Time Purchase`: Non-recurring purchase
  - `Upgrade`: Increase in subscription level
  - `Downgrade`: Decrease in subscription level
  - `Add-on`: Additional service or feature purchase
- **Validation Rules**: Must be one of the defined values, must not be null.
- **Analysis Considerations**: Subscription transactions form the basis of MRR calculations.

### `subscription_plan`

- **Business Purpose**: Identifies the product tier for revenue segmentation and pricing analysis.
- **Source**: Assigned based on customer's subscription choice.
- **Valid Values**:
  - `Free`: No-cost tier
  - `Basic`: Entry-level paid plan
  - `Pro`: Mid-tier plan for professionals
  - `Enterprise`: High-tier plan for large organizations
  - `Custom`: Custom-priced plan for specific customers
- **Validation Rules**: Must be one of the defined values when transaction_type is 'Subscription'.
- **Analysis Considerations**: Used for analyzing plan distribution and upgrade paths.

### `category`

- **Business Purpose**: Classifies transactions for financial reporting and accounting.
- **Source**: Assigned based on transaction purpose.
- **Valid Values**:
  - `Revenue`: Income from sales
  - `Marketing Cost`: Expenses related to marketing activities
  - `Operational Expense`: General operating costs
  - `Infrastructure Cost`: Technology and infrastructure expenses
  - `Customer Support`: Costs associated with supporting customers
  - `R&D`: Research and development expenses
  - `Administrative`: General administrative costs
- **Validation Rules**: Must be one of the defined values, must not be null.
- **Analysis Considerations**: Used for P&L statements and expense analysis.

### `region`

- **Business Purpose**: Captures geographic location for regional performance analysis.
- **Source**: Derived from customer billing address.
- **Valid Values**:
  - `US`: United States
  - `EU`: European Union
  - `APAC`: Asia-Pacific region
  - `LATAM`: Latin America
  - `MEA`: Middle East and Africa
- **Validation Rules**: Must be one of the defined values if present.
- **Analysis Considerations**: Used for regional performance comparisons.

### `payment_status`

- **Business Purpose**: Tracks the status of payment transactions for revenue recognition and cash flow analysis.
- **Source**: Updated based on payment processing status.
- **Valid Values**:
  - `Completed`: Payment successfully processed
  - `Pending`: Payment initiated but not confirmed
  - `Failed`: Payment attempt unsuccessful
  - `Refunded`: Payment returned to customer
  - `Disputed`: Payment challenged by customer
- **Validation Rules**: Must be one of the defined values, must not be null.
- **Analysis Considerations**: Only 'Completed' transactions should be counted in recognized revenue.

### `customer_type`

- **Business Purpose**: Segments customers by business size for targeted analysis.
- **Source**: Assigned based on customer attributes or self-selection.
- **Valid Values**:
  - `B2C`: Business-to-Consumer (individual customers)
  - `SMB`: Small and Medium Businesses
  - `Mid-Market`: Mid-sized organizations
  - `Enterprise`: Large enterprises
- **Validation Rules**: Must be one of the defined values if present.
- **Analysis Considerations**: Used for segmentation analysis and targeted strategies.

## Common Queries and Metrics

### Monthly Recurring Revenue (MRR)
```sql
SELECT 
  DATE_TRUNC(timestamp, MONTH) AS month, 
  SUM(amount) AS mrr
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE 
  transaction_type = 'Subscription'
  AND category = 'Revenue'
  AND payment_status = 'Completed'
GROUP BY month
ORDER BY month;
```

### Customer Retention Rate
```sql
WITH customer_months AS (
  SELECT
    customer_id,
    DATE_TRUNC(timestamp, MONTH) AS month
  FROM `financial-reporting-pipeline.financial_data.transactions`
  WHERE 
    transaction_type = 'Subscription'
    AND category = 'Revenue'
  GROUP BY customer_id, month
)
SELECT
  curr.month,
  COUNT(DISTINCT curr.customer_id) AS current_customers,
  COUNT(DISTINCT prev.customer_id) AS retained_customers,
  ROUND(COUNT(DISTINCT prev.customer_id) / COUNT(DISTINCT curr.customer_id) * 100, 2) AS retention_rate
FROM customer_months curr
LEFT JOIN customer_months prev
  ON curr.customer_id = prev.customer_id
  AND prev.month = DATE_SUB(curr.month, INTERVAL 1 MONTH)
GROUP BY curr.month
ORDER BY curr.month;
```

### Revenue by Customer Segment
```sql
SELECT
  customer_type,
  SUM(amount) AS total_revenue,
  COUNT(DISTINCT customer_id) AS customer_count,
  SUM(amount) / COUNT(DISTINCT customer_id) AS avg_revenue_per_customer
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE 
  category = 'Revenue'
  AND payment_status = 'Completed'
GROUP BY customer_type
ORDER BY total_revenue DESC;
```

## Data Lineage

1. **Source Data**: Generated by the synthetic data generation script `generate_synthetic_data.py`
2. **Ingestion**: Loaded into BigQuery using the ETL script `load_data_to_bigquery.py`
3. **Transformation**: Processed through SQL queries to create derived tables
4. **Visualization**: Displayed in Looker dashboards for business analysis

## Governance and Access Control

- Financial data is sensitive and should be handled according to the company's data governance policies
- Access to the raw transactions table should be limited to the Finance team and Data Engineering team
- Derived aggregated tables may have broader access for business intelligence purposes
- All queries against the transactions table should be logged for audit purposes

## Data Quality Rules

1. **Completeness**: All required fields must be populated
2. **Validity**: Field values must conform to their defined domains
3. **Consistency**: Related fields must be logically consistent (e.g., transaction_type and subscription_plan)
4. **Timeliness**: Transactions should be loaded within 24 hours of occurrence
5. **Accuracy**: Amount values must accurately reflect the financial transaction

## Maintenance and Updates

This data dictionary should be reviewed and updated when:
- New fields are added to the data model
- Field definitions or valid values change
- New derived tables are created
- Business metrics definitions are modified

**Last Updated**: May 21, 2025  
**Document Owner**: Analytics Engineering Team
