import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import logging
import os
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"bigquery_load_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_data_to_bigquery(csv_file, project_id, dataset_id, table_id, key_path):
    """
    Load data from a CSV file to BigQuery with error handling and schema definition.
    
    Parameters:
    -----------
    csv_file : str
        Path to the CSV file to load
    project_id : str
        Google Cloud project ID
    dataset_id : str
        BigQuery dataset ID
    table_id : str
        BigQuery table ID
    key_path : str
        Path to service account key JSON file
    
    Returns:
    --------
    bool
        True if load was successful, False otherwise
    """
    try:
        start_time = datetime.now()
        logger.info(f"Starting BigQuery load process for {csv_file}")
        
        # Check if the CSV file exists
        if not os.path.exists(csv_file):
            logger.error(f"CSV file not found: {csv_file}")
            return False
        
        # Load the CSV file into a pandas DataFrame
        logger.info("Reading CSV file into DataFrame")
        df = pd.read_csv(csv_file)
        
        # Log basic data stats
        logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
        logger.info(f"Columns: {', '.join(df.columns)}")
        
        # Check for missing values in critical columns
        critical_columns = ['transaction_id', 'timestamp', 'customer_id', 'amount']
        for col in critical_columns:
            if col in df.columns and df[col].isnull().sum() > 0:
                null_count = df[col].isnull().sum()
                logger.warning(f"Found {null_count} null values in critical column {col}")
        
        # Convert timestamp strings to datetime objects
        if 'timestamp' in df.columns:
            logger.info("Converting timestamp column to datetime")
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Define schema for BigQuery table
        schema = [
            bigquery.SchemaField("transaction_id", "STRING", mode="REQUIRED", description="Unique transaction identifier"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED", description="Transaction datetime"),
            bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED", description="Customer identifier"),
            bigquery.SchemaField("amount", "FLOAT", mode="REQUIRED", description="Transaction amount"),
            bigquery.SchemaField("transaction_type", "STRING", description="Type of transaction"),
            bigquery.SchemaField("subscription_plan", "STRING", description="Subscription plan type"),
            bigquery.SchemaField("category", "STRING", description="Transaction category"),
            bigquery.SchemaField("region", "STRING", description="Geographic region"),
            bigquery.SchemaField("payment_status", "STRING", description="Payment status"),
            bigquery.SchemaField("customer_type", "STRING", description="Type of customer")
        ]
        
        # Initialize BigQuery client
        logger.info(f"Initializing BigQuery client with service account: {key_path}")
        client = bigquery.Client.from_service_account_json(key_path)
        
        # Create table reference
        full_table_id = f"{project_id}.{dataset_id}.{table_id}"
        logger.info(f"Target table: {full_table_id}")
        
        # Check if dataset exists, create if not
        try:
            client.get_dataset(dataset_id)
            logger.info(f"Dataset {dataset_id} exists")
        except Exception:
            logger.info(f"Dataset {dataset_id} not found, creating...")
            dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
            dataset.location = "US"  # Set the geographic location
            client.create_dataset(dataset)
            
        # Configure load job
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Replace existing table data
            time_partitioning=bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.MONTH,
                field="timestamp"  # Partition by month based on timestamp
            ),
            clustering_fields=["region", "customer_type", "transaction_type"]  # Cluster for faster queries
        )
        
        # Start the load job
        logger.info("Starting BigQuery load job")
        load_job = client.load_table_from_dataframe(
            df, full_table_id, job_config=job_config
        )
        
        # Wait for job to complete
        logger.info("Waiting for job to complete...")
        load_job.result()  # Waits for job to complete
        
        # Validate results
        table = client.get_table(full_table_id)
        logger.info(f"Loaded {table.num_rows} rows to {full_table_id}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Load completed successfully in {duration:.2f} seconds")
        return True
        
    except GoogleCloudError as e:
        logger.error(f"Google Cloud error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    # Configuration
    CSV_FILE = 'synthetic_saas_financial_data.csv'
    PROJECT_ID = 'financial-reporting-pipeline'
    DATASET_ID = 'financial_data'
    TABLE_ID = 'transactions'
    KEY_PATH = 'key.json'
    
    # Execute load process
    success = load_data_to_bigquery(
        csv_file=CSV_FILE,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        table_id=TABLE_ID,
        key_path=KEY_PATH
    )
    
    if success:
        logger.info("✅ Data loading completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Data loading failed")
        sys.exit(1)
