import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
import uuid

def generate_synthetic_saas_data(num_rows=15000, start_date='2023-01-01', end_date='2025-05-20'):
    """
    Generate synthetic SaaS financial transaction data.
    
    Parameters:
    -----------
    num_rows : int
        Number of transactions to generate
    start_date : str
        Start date for transactions in 'YYYY-MM-DD' format
    end_date : str
        End date for transactions in 'YYYY-MM-DD' format
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing synthetic SaaS financial data
    """
    # Convert date strings to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Define possible values for categorical fields
    transaction_types = ['Subscription', 'Refund', 'One-Time Purchase', 'Upgrade', 'Downgrade', 'Add-on']
    subscription_plans = ['Free', 'Basic', 'Pro', 'Enterprise', 'Custom']
    plan_prices = {'Free': 0, 'Basic': 19.99, 'Pro': 49.99, 'Enterprise': 199.99, 'Custom': 499.99}
    
    categories = ['Revenue', 'Marketing Cost', 'Operational Expense', 'Infrastructure Cost', 
                  'Customer Support', 'R&D', 'Administrative']
    
    regions = ['US', 'EU', 'APAC', 'LATAM', 'MEA']
    region_weights = [0.45, 0.25, 0.15, 0.1, 0.05]  # US has highest probability
    
    payment_statuses = ['Completed', 'Pending', 'Failed', 'Refunded', 'Disputed']
    status_weights = [0.9, 0.05, 0.03, 0.015, 0.005]  # Most payments complete successfully
    
    customer_types = ['B2C', 'SMB', 'Mid-Market', 'Enterprise']
    customer_type_weights = [0.6, 0.25, 0.1, 0.05]  # B2C most common
    
    # Generate a realistic number of customers (fewer than transactions)
    num_customers = int(num_rows / 10)  # Each customer has ~10 transactions on average
    customer_ids = [f'CUST_{str(i).zfill(6)}' for i in range(1, num_customers + 1)]
    
    # Assign customer types to customer IDs
    customer_type_map = {cid: np.random.choice(customer_types, p=customer_type_weights) 
                         for cid in customer_ids}
    
    # Assign subscription plans to customers based on customer type
    def assign_plan(ctype):
        if ctype == 'B2C':
            return np.random.choice(['Free', 'Basic', 'Pro'], p=[0.6, 0.3, 0.1])
        elif ctype == 'SMB':
            return np.random.choice(['Basic', 'Pro'], p=[0.7, 0.3])
        elif ctype == 'Mid-Market':
            return np.random.choice(['Pro', 'Enterprise'], p=[0.7, 0.3])
        else:  # Enterprise
            return np.random.choice(['Enterprise', 'Custom'], p=[0.6, 0.4])
    
    customer_plan_map = {cid: assign_plan(ctype) for cid, ctype in customer_type_map.items()}
    
    # Generate data
    data = []
    
    # Generate transactions in chronological order
    date_range = (end_date - start_date).days
    sorted_dates = [start_date + timedelta(days=np.random.randint(date_range)) 
                   for _ in range(num_rows)]
    sorted_dates.sort()
    
    # Add a time component to make timestamps
    timestamps = [date + timedelta(hours=random.randint(8, 20), 
                                   minutes=random.randint(0, 59), 
                                   seconds=random.randint(0, 59)) 
                 for date in sorted_dates]
    
    for i in range(num_rows):
        # Get customer ID and their associated type and plan
        customer_id = np.random.choice(customer_ids)
        customer_type = customer_type_map[customer_id]
        customer_plan = customer_plan_map[customer_id]
        
        # Determine transaction type
        if i > 0 and random.random() < 0.1:  # 10% chance for non-subscription transactions
            tx_type = np.random.choice(['Refund', 'One-Time Purchase', 'Upgrade', 'Downgrade', 'Add-on'])
        else:
            tx_type = 'Subscription'
        
        # Set the category based on transaction type
        if tx_type in ['Subscription', 'One-Time Purchase', 'Upgrade', 'Add-on']:
            category = 'Revenue'
        elif tx_type == 'Refund':
            category = 'Revenue'  # Negative revenue
        else:
            category = np.random.choice(['Marketing Cost', 'Operational Expense', 'Infrastructure Cost', 
                                      'Customer Support', 'R&D', 'Administrative'])
        
        # Set amount based on transaction type and plan
        base_price = plan_prices[customer_plan]
        if category == 'Revenue':
            if tx_type == 'Subscription':
                amount = base_price
            elif tx_type == 'Upgrade':
                amount = random.uniform(10, 100)  # Additional amount
            elif tx_type == 'Add-on':
                amount = random.uniform(5, 50)
            elif tx_type == 'One-Time Purchase':
                amount = random.uniform(20, 500)
            elif tx_type == 'Refund':
                amount = -base_price * random.uniform(0.1, 1.0)  # Partial or full refund
            else:  # Downgrade
                amount = -random.uniform(10, 100)  # Reduction amount
        else:
            # Expenses
            if category == 'Marketing Cost':
                amount = -random.uniform(10, 5000)
            elif category == 'Infrastructure Cost':
                amount = -random.uniform(50, 2000)
            else:
                amount = -random.uniform(20, 1000)
        
        # Generate other fields
        region = np.random.choice(regions, p=region_weights)
        payment_status = np.random.choice(payment_statuses, p=status_weights)
        
        # Add some seasonality/patterns for more realistic data
        timestamp = timestamps[i]
        # End of month spike for subscriptions
        if timestamp.day >= 25 and tx_type == 'Subscription':
            amount *= random.uniform(1.0, 1.2)  # 0-20% increase
        # December holiday spending
        if timestamp.month == 12:
            amount *= random.uniform(1.1, 1.3)  # 10-30% increase for holiday season
        
        # Transaction ID with prefix based on type
        prefix = 'REV_' if category == 'Revenue' else 'EXP_'
        transaction_id = f"{prefix}{str(uuid.uuid4()).replace('-', '')[:12].upper()}"
        
        data.append({
            'transaction_id': transaction_id,
            'timestamp': timestamp,
            'customer_id': customer_id,
            'amount': round(amount, 2),
            'transaction_type': tx_type,
            'subscription_plan': customer_plan,
            'category': category,
            'region': region,
            'payment_status': payment_status,
            'customer_type': customer_type
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Add some failed payments and disputes for realism
    # For failed payments, create corresponding successful payments later (retry)
    failed_indices = df[df['payment_status'] == 'Failed'].index
    for idx in failed_indices:
        if random.random() < 0.7:  # 70% of failed payments are retried successfully
            failed_row = df.loc[idx].copy()
            retry_date = failed_row['timestamp'] + timedelta(days=random.randint(1, 7))
            if retry_date <= end_date:
                failed_row['timestamp'] = retry_date
                failed_row['payment_status'] = 'Completed'
                failed_row['transaction_id'] = f"RETRY_{failed_row['transaction_id'][4:]}"
                df = pd.concat([df, pd.DataFrame([failed_row])], ignore_index=True)
    
    # Sort by timestamp for final dataset
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Ensure we don't exceed the requested number of rows
    if len(df) > num_rows:
        df = df.sample(num_rows, random_state=42)
        df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df

# Generate the dataset
np.random.seed(42)  # For reproducibility
random.seed(42)

num_rows = random.randint(10000, 20000)
dataset = generate_synthetic_saas_data(num_rows=num_rows)

# Save to CSV
output_file = 'financial_data.csv'
dataset.to_csv(output_file, index=False)

# Display some statistics
print(f"Generated {len(dataset)} rows of synthetic SaaS financial data")
print(f"Date range: {dataset['timestamp'].min()} to {dataset['timestamp'].max()}")
print(f"Number of unique customers: {dataset['customer_id'].nunique()}")
print(f"Revenue transactions: {len(dataset[dataset['category'] == 'Revenue'])}")
print(f"Expense transactions: {len(dataset[dataset['category'] != 'Revenue'])}")
print(f"Distribution by customer type:")
print(dataset['customer_type'].value_counts())
print(f"Distribution by subscription plan:")
print(dataset['subscription_plan'].value_counts())
print(f"Data saved to {output_file}")
