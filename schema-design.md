# Schema Design Documentation

## Overview

This document outlines the design decisions for the SaaS financial analytics data schema. The schema is optimized for financial reporting, SaaS metrics calculation, and business intelligence within a distributed global company environment like Automattic.

## Primary Table Design: `transactions`

The transactions table serves as the central fact table in our data model, capturing all financial events across the business.

### Design Principles

1. **Single Source of Financial Truth**: All financial transactions are captured in a single table to simplify querying and ensure consistency.

2. **Analytical Readiness**: The schema is designed for analytical workloads with properly typed fields and categorization dimensions.

3. **Performance Optimization**: Partitioning and clustering are implemented to optimize query performance for typical analytical patterns.

4. **Data Integrity**: Required fields and constraints ensure data quality.

5. **Multi-dimensional Analysis**: Categorical fields enable slicing and dicing across multiple business dimensions.

### Schema Structure

```python
schema = [
    # Primary key and required fields
    bigquery.SchemaField("transaction_id", "STRING", mode="REQUIRED", 
                         description="Unique transaction identifier for financial events"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED", 
                         description="Date and time when the transaction occurred (used for partitioning)"),
    bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED", 
                         description="Unique identifier for customers or accounts"),
    bigquery.SchemaField("amount", "FLOAT", mode="REQUIRED", 
                         description="Monetary value of the transaction (positive for revenue, negative for expenses)"),
    
    # Categorical fields for dimensions and aggregations
    bigquery.SchemaField("transaction_type", "STRING", mode="REQUIRED",
                         description="Type of transaction (Subscription, Refund, One-Time Purchase, Upgrade, Downgrade, Add-on)"),
    bigquery.SchemaField("subscription_plan", "STRING", 
                         description="SaaS plan associated with the transaction (Free, Basic, Pro, Enterprise, Custom)"),
    bigquery.SchemaField("category", "STRING", mode="REQUIRED",
                         description="Financial category for accounting (Revenue, Marketing Cost, Operational Expense, etc.)"),
    bigquery.SchemaField("region", "STRING", 
                         description="Geographic region of the customer (US, EU, APAC, LATAM, MEA)"),
    bigquery.SchemaField("payment_status", "STRING", mode="REQUIRED",
                         description="Status of the payment transaction (Completed, Pending, Failed, Refunded, Disputed)"),
    bigquery.SchemaField("customer_type", "STRING", 
                         description="Business segment of the customer (B2C, SMB, Mid-Market, Enterprise)")
]
```

## Performance Optimization

### Partitioning Strategy

The table is partitioned by the `timestamp` field using monthly partitioning:

```python
time_partitioning=bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.MONTH,
    field="timestamp"
)
```

**Rationale:**
- Financial analysis is typically time-based (monthly, quarterly, yearly)
- Monthly partitioning aligns with common SaaS reporting cycles
- Reduces query costs by scanning only relevant time periods
- Improves query performance for time-based analysis

### Clustering Strategy

The table is clustered by three fields in priority order:

```python
clustering_fields=["region", "customer_type", "transaction_type"]
```

**Rationale:**
- **Region**: Geographic segmentation is a primary dimension for a global company like Automattic
- **Customer Type**: Business segment analysis is critical for understanding performance across B2C to Enterprise
- **Transaction Type**: Enables efficient filtering for specific transaction types like subscriptions or refunds

This clustering strategy optimizes for common query patterns:
- Regional financial performance
- Segment-based analysis
- Transaction type filtering (e.g., subscription revenue only)

## Field Design Decisions

### Key Field Design Choices

1. **transaction_id (STRING)**:
   - Uses STRING type to accommodate prefixed IDs with potential alphanumeric formats
   - Required field to ensure data integrity

2. **amount (FLOAT)**:
   - Uses floating-point for currency values to handle decimal precision
   - Employs sign convention (positive = revenue, negative = expense)
   - Enables direct aggregation into net metrics without filtering

3. **timestamp (TIMESTAMP)**:
   - Full timestamp rather than just date to support intraday analysis
   - Used for both chronological ordering and partitioning
   - Enables time-based aggregation at various levels (day/month/quarter/year)

4. **category (STRING, REQUIRED)**:
   - Enforces financial categorization for accounting alignment
   - Supports financial statement preparation (income statement, cash flow)
   - Required to ensure proper classification

## Schema Evolution Design

The schema is designed to accommodate future evolution through:

1. **Nullable Fields**: Non-critical fields are defined as nullable to ensure backward compatibility

2. **Extensible Dimensions**: Categorical fields can accept new values without schema changes

3. **Semantic Types**: Fields use broad semantic types (e.g., STRING for IDs) to accommodate format changes

## Query Performance Considerations

The schema is optimized for these common financial analytics query patterns:

1. **Time-Series Analysis**:
   ```sql
   SELECT DATE_TRUNC(timestamp, MONTH) AS month, SUM(amount) AS revenue
   FROM transactions 
   WHERE category = 'Revenue' AND timestamp BETWEEN '2023-01-01' AND '2023-12-31'
   GROUP BY month
   ORDER BY month
   ```
   Optimization: Timestamp partitioning reduces data scanned

2. **Segment Analysis**:
   ```sql
   SELECT customer_type, COUNT(DISTINCT customer_id) AS customer_count, SUM(amount) AS revenue
   FROM transactions
   WHERE category = 'Revenue' AND region = 'US'
   GROUP BY customer_type
   ```
   Optimization: Clustering by region and customer_type improves performance

3. **SaaS Metrics**:
   ```sql
   SELECT subscription_plan, SUM(amount) AS mrr
   FROM transactions
   WHERE transaction_type = 'Subscription' AND DATE_TRUNC(timestamp, MONTH) = '2023-05-01'
   GROUP BY subscription_plan
   ```
   Optimization: Clustering by transaction_type improves filtering performance

## Future Schema Recommendations

For production implementation, consider these enhancements:

1. **Dimensional Model**: 
   - Implement proper dimension tables for customers, products, geography
   - Add foreign key relationships to the fact table

2. **Audit Fields**:
   - Add created_at, updated_at timestamps for data lineage
   - Include ETL job ID for process tracking

3. **Derived Fields**:
   - Add pre-calculated fields for common metrics
   - Include fiscal period field aligned with accounting calendar

4. **Data Governance**:
   - Add field-level access controls for sensitive financial data
   - Implement row-level security for regional data access

5. **Additional Metadata**:
   - Add data classification tags
   - Include data quality score fields
