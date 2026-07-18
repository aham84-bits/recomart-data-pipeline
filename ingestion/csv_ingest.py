# Ingests CSV data from REES46 e-commerce events file
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
import os
from ingestion.logger_config import get_logger

logger = get_logger(__name__)

def clean_events(df):
    # Clean the dataframe by removing invalid rows
    
    initial_rows = len(df)
    
    # Skip rows where price is missing or <= 0
    df = df.dropna(subset=['price'])
    df = df[df['price'] > 0]
    price_dropped = initial_rows - len(df)
    
    # Skip rows where event_time is a future date
    current_date = datetime.now()
    df['event_time'] = pd.to_datetime(df['event_time'], errors='coerce')
    df = df.dropna(subset=['event_time'])
    df = df[df['event_time'] <= current_date]
    future_dropped = initial_rows - price_dropped - len(df)
    
    # Drop exact duplicate rows
    before_dedup = len(df)
    df = df.drop_duplicates()
    dup_dropped = before_dedup - len(df)
    
    # Log how many rows were dropped and why
    logger.info(f"Cleaned data: dropped {price_dropped} rows with invalid price")
    logger.info(f"Cleaned data: dropped {future_dropped} rows with future dates")
    logger.info(f"Cleaned data: dropped {dup_dropped} duplicate rows")
    logger.info(f"Cleaned data: kept {len(df)} rows out of {initial_rows} total")
    
    return df

def load_events():
    # Load and clean the events CSV file
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, 'data/raw/events.csv')
    output_path = os.path.join(base_dir, 'data/raw/events_clean.csv')
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.join(base_dir, 'data/raw'), exist_ok=True)
        
        logger.info(f"Starting to read events from {input_path}")
        
        # Read the CSV in chunks to avoid loading everything into memory
        chunksize = 100000
        chunks = []
        total_rows_read = 0
        
        for chunk in pd.read_csv(input_path, chunksize=chunksize):
            total_rows_read += len(chunk)
            logger.info(f"Read chunk of {len(chunk)} rows")
            
            # Clean this chunk
            cleaned_chunk = clean_events(chunk)
            chunks.append(cleaned_chunk)
        
        # Combine all cleaned chunks
        logger.info(f"Total rows read from file: {total_rows_read}")
        df = pd.concat(chunks, ignore_index=True)
        
        # Save the cleaned data
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to {output_path}")
        logger.info(f"Final cleaned data has {len(df)} rows")
        
        return df
        
    except FileNotFoundError:
        logger.error(f"File not found: {input_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        return None

if __name__ == "__main__":
    load_events()
