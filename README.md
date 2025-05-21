# SaaS Financial Analytics Pipeline

## Project Overview

This repository contains a complete data pipeline for financial analytics in a SaaS business model, designed to demonstrate the skills required for an Analytics Engineer role at Automattic. The project simulates the entire data lifecycle from synthetic data generation to ETL processing, data modeling, and visualization.

As Automattic's Analytics Engineer for Finance, this pipeline would support key responsibilities including:
- Building reliable ETL processes for financial data
- Designing metrics to monitor business performance
- Creating high-quality analyses and dashboards to communicate insights
- Ensuring data quality and integrity
- Enabling self-service analytics for finance teams

## Tech Stack

- **Python**: Data generation and BigQuery integration
- **Google BigQuery**: Data warehousing and analytics, including anomaly detection with BigQuery ML
- **Looker**: Data visualization and dashboards
- **Git**: Version control and code management

## Repository Structure

```
financial-analytics-pipeline/
├── data_generator/
│   └── Financial Data Generator.py        # Script to generate SaaS financial data
├── bigquery/
│   ├── schema/
│   │   └── transactions_schema.json      # Schema definition for the main table
│   ├── etl/
│       └── load_data_to_bigquery.py      # ETL script with error handling and logging
├── sql/
│       └── monthly metrics.sql           # MRR calculation and active customers
│       ├── data quality_check.sql        # Data validation and quality monitoring
│       ├── anomaly_detection.sql         # ML model for detecting payment anomalies
│       ├── retention analysis.sql        # Customer retention by cohort
│       ├── revenue recognition.sql       # Revenue recognition by month and plan
│       └── customer segmentation.sql     # Customer analysis by segment and region
├── documentation/
│   ├── data_dictionary.md                # Comprehensive data dictionary
│   ├── metrics_definitions.md            # SaaS metrics definitions and calculations
│   └── schema_design.md                  # Schema design decisions and rationale
└── README.md                             # This file
```

## Key Features

### 1. Synthetic Data Generation

The project starts with a Python script that generates realistic SaaS financial data with:
- Transaction-level granularity
- Subscription revenue patterns with monthly/annual cycles
- Customer segments across different plan types
- Geographic distribution
- Realistic cost and expense patterns

### 2. Data Warehouse Implementation

The BigQuery implementation includes:
- Proper schema design with field typing and descriptions
- Table partitioning by timestamp for performance optimization
- Table clustering by region, customer type, and transaction type
- Data quality checks and validation
- ETL process with comprehensive error handling and logging

### 3. Financial Analytics Capabilities

The SQL queries demonstrate key financial analytics capabilities:
- **MRR/ARR Calculation**: Monthly and annual recurring revenue metrics
- **Retention Analysis**: Cohort-based customer retention analysis
- **Customer Segmentation**: Analysis by customer type, region, and plan
- **Anomaly Detection**: Using BigQuery ML to identify unusual payment patterns
- **Revenue Recognition**: Financial reporting aligned with accounting principles

### 4. Dashboard Visualization

![Financial Analysis Dashboard](https://github.com/user-attachments/assets/da1ae212-c5ea-4604-a392-780aa3d6c7bb)


The Looker dashboard (link available upon request) includes:
- Executive summary with key SaaS metrics
- Trend analysis for financial performance
- Customer segment analysis
- Geographic performance breakdown
- Retention and churn visualization

## Data Model

The central fact table contains financial transactions with these key attributes:
- **transaction_id**: Unique identifier for each transaction
- **timestamp**: When the transaction occurred
- **customer_id**: Identifier linking to customer information
- **amount**: Monetary value (positive for revenue, negative for expenses)
- **transaction_type**: Categorizes the transaction (Subscription, Refund, etc.)
- **subscription_plan**: Associated SaaS plan
- **category**: Financial classification for accounting
- **region**: Geographic location
- **payment_status**: Transaction status
- **customer_type**: Business segment classification

This model supports both transactional analysis and aggregation into SaaS metrics like MRR, customer lifetime value, and churn rate.

## Sample Queries and Insights

### Monthly Recurring Revenue (MRR)
```sql
SELECT DATE_TRUNC(timestamp, MONTH) AS month, 
       SUM(amount) AS mrr,
       COUNT(DISTINCT customer_id) AS active_customers
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE transaction_type = 'Subscription'
GROUP BY month;
```

### Data Quality Monitoring
```sql
SELECT COUNT(*) AS null_count
FROM `financial-reporting-pipeline.financial_data.transactions`
WHERE transaction_id IS NULL OR timestamp IS NULL OR amount IS NULL;
```

### Anomaly Detection with ML
```sql
SELECT t.*, m.centroid_id
FROM `financial-reporting-pipeline.financial_data.transactions` t
JOIN ML.PREDICT(MODEL `financial-reporting-pipeline.financial_data.anomaly_model`, 
                (SELECT amount FROM `financial-reporting-pipeline.financial_data.transactions` WHERE payment_status = 'Failed')) m
ON t.amount = m.amount
WHERE m.centroid_id = 1;
```

## Business Impact

This analytics pipeline would support key business functions at Automattic:

1. **Financial Planning & Analysis**:
   - Accurate revenue forecasting
   - Expense tracking and categorization
   - Budget vs. actual analysis

2. **Product Strategy**:
   - Plan performance and pricing optimization
   - Feature adoption and upgrade paths
   - Customer segmentation insights

3. **Executive Decision Making**:
   - Consolidated KPI reporting
   - Performance trend analysis
   - Market segment optimization

## Next Steps & Future Enhancements

With additional time, these enhancements would be valuable:

1. **Data Architecture**:
   - Implement a full dimensional model with star schema
   - Add data lineage tracking
   - Create dbt transformations for modularity

2. **Advanced Analytics**:
   - Churn prediction modeling
   - Customer lifetime value forecasting
   - Scenario analysis for pricing changes

3. **Automation**:
   - Airflow DAGs for pipeline orchestration
   - Automated data quality monitoring
   - CI/CD integration for analytics code

## About This Project

This project was developed to demonstrate financial analytics engineering capabilities for a SaaS business model. It addresses key requirements from the Analytics Engineer role at Automattic, including SQL proficiency, programming skills, data visualization expertise, and experience with financial data and large datasets.

The implementation demonstrates how financial data can be transformed into actionable insights to support decision-making in a distributed, global company with diverse business models and customer segments.
