# Uploads cleaned data from ingestion stage to partitioned storage layout
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import pandas as pd
from datetime import datetime
from ingestion.logger_config import get_logger

logger = get_logger(__name__)

def load_config():
    # Load the storage configuration from yaml file
    config_path = os.path.join(os.path.dirname(__file__), 'storage_config.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded config from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found at {config_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return None

def partition_events(config):
    # Read events csv and partition by year/month/day
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, config['input']['events'])
    base_path = os.path.join(base_dir, config['base_path'])
    
    try:
        logger.info(f"Reading events from {input_path}")
        df = pd.read_csv(input_path)
        logger.info(f"Read {len(df)} events from CSV")
        
        # Parse event_time as datetime
        df['event_time'] = pd.to_datetime(df['event_time'])
        
        # Extract year, month, day for partitioning
        df['year'] = df['event_time'].dt.year
        df['month'] = df['event_time'].dt.month
        df['day'] = df['event_time'].dt.day
        
        # Group by date partitions
        grouped = df.groupby(['year', 'month', 'day'])
        
        total_partitions = 0
        total_rows = 0
        
        # Write each partition to its own folder
        for (year, month, day), group in grouped:
            # Build the partition folder path
            partition_path = os.path.join(base_path, 'events', f'year={year}', f'month={month:02d}', f'day={day:02d}')
            output_file = os.path.join(partition_path, 'events.parquet')
            
            # Check if file already exists
            if os.path.exists(output_file):
                logger.warning(f"Partition already exists, skipping: {output_file}")
                continue
            
            # Create directory if it doesn't exist
            os.makedirs(partition_path, exist_ok=True)
            
            # Write to parquet
            group.to_parquet(output_file, index=False)
            logger.info(f"Wrote {len(group)} rows to {output_file}")
            
            total_partitions += 1
            total_rows += len(group)
        
        return total_partitions, total_rows
        
    except FileNotFoundError:
        logger.error(f"Events file not found: {input_path}")
        return 0, 0
    except Exception as e:
        logger.error(f"Error processing events: {str(e)}")
        return 0, 0

def partition_users(config):
    # Read users json and write to snapshot folder
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, config['input']['users'])
    base_path = os.path.join(base_dir, config['base_path'])
    
    try:
        logger.info(f"Reading users from {input_path}")
        df = pd.read_json(input_path)
        logger.info(f"Read {len(df)} users from JSON")
        
        # Get today's date for the snapshot folder
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Build the partition folder path
        partition_path = os.path.join(base_path, 'users', f'snapshot_date={today}')
        output_file = os.path.join(partition_path, 'users.parquet')
        
        # Check if file already exists
        if os.path.exists(output_file):
            logger.warning(f"Users partition already exists, skipping: {output_file}")
            return 0, 0
        
        # Create directory if it doesn't exist
        os.makedirs(partition_path, exist_ok=True)
        
        # Write to parquet
        df.to_parquet(output_file, index=False)
        logger.info(f"Wrote {len(df)} rows to {output_file}")
        
        return 1, len(df)
        
    except FileNotFoundError:
        logger.error(f"Users file not found: {input_path}")
        return 0, 0
    except Exception as e:
        logger.error(f"Error processing users: {str(e)}")
        return 0, 0

def main():
    # Main function to run the upload process
    logger.info("Starting storage upload process")
    
    # Load configuration
    config = load_config()
    if config is None:
        logger.error("Failed to load config, exiting")
        return
    
    # Process events
    logger.info("Processing events partitioning")
    event_partitions, event_rows = partition_events(config)
    
    # Process users
    logger.info("Processing users partitioning")
    user_partitions, user_rows = partition_users(config)
    
    # Print summary
    total_partitions = event_partitions + user_partitions
    total_rows = event_rows + user_rows
    
    logger.info("=" * 50)
    logger.info("SUMMARY:")
    logger.info(f"Total partitions written: {total_partitions}")
    logger.info(f"Total rows written: {total_rows}")
    logger.info(f"  - Events: {event_partitions} partitions, {event_rows} rows")
    logger.info(f"  - Users: {user_partitions} partitions, {user_rows} rows")
    logger.info("=" * 50)
    
    logger.info("Storage upload process completed")

if __name__ == "__main__":
    main()
