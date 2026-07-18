# Validates and profiles the partitioned data, outputs cleaned files and data quality report
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import glob
import json
from datetime import datetime
from ingestion.logger_config import get_logger

logger = get_logger(__name__)

def load_events():
    # Read all events parquet partitions using glob
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    events_pattern = os.path.join(base_dir, 'storage/raw/events/year=*/month=*/day=*/events.parquet')
    events_files = glob.glob(events_pattern)
    
    if not events_files:
        logger.error(f"No events parquet files found at {events_pattern}")
        return None
    
    logger.info(f"Found {len(events_files)} events partition files")
    
    # Read and concatenate all partitions
    dfs = []
    for file in events_files:
        df = pd.read_parquet(file)
        dfs.append(df)
    
    events_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(events_df)} events rows from parquet partitions")
    
    return events_df

def load_users():
    # Read the latest users snapshot parquet
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    users_pattern = os.path.join(base_dir, 'storage/raw/users/snapshot_date=*/users.parquet')
    users_files = glob.glob(users_pattern)
    
    if not users_files:
        logger.error(f"No users parquet files found at {users_pattern}")
        return None
    
    # Get the most recent snapshot by sorting by path (date is in the path)
    users_files.sort()
    latest_file = users_files[-1]
    
    logger.info(f"Loading users from latest snapshot: {latest_file}")
    users_df = pd.read_parquet(latest_file)
    logger.info(f"Loaded {len(users_df)} users rows")
    
    return users_df

def build_products(events_df):
    # Build products table from events by grouping by product_id
    # Take the most recent category_code, brand, and price for each product_id
    logger.info("Building products table from events data")
    
    # Sort by event_time to get most recent values first
    events_sorted = events_df.sort_values('event_time')
    
    # Group by product_id and take the last (most recent) values
    products_df = events_sorted.groupby('product_id').agg({
        'category_code': 'last',
        'brand': 'last',
        'price': 'last'
    }).reset_index()
    
    logger.info(f"Built products table with {len(products_df)} unique products")
    
    return products_df

def profile_missing_values(df, table_name):
    # Count missing values per column
    missing_counts = {}
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_counts[col] = missing_count
        if missing_count > 0:
            logger.info(f"{table_name}: {missing_count} missing values in column '{col}'")
    
    # Special handling for users - check if city is missing from address
    if table_name == 'Users' and 'address' in df.columns:
        missing_city = df['address'].apply(lambda x: not isinstance(x, dict) or not x.get('city')).sum()
        missing_counts['city_from_address'] = missing_city
        if missing_city > 0:
            logger.info(f"Users: {missing_city} rows with missing city in address")
    
    return missing_counts

def profile_duplicates(events_df, users_df, products_df):
    # Count duplicates in each table
    dup_results = {}
    
    # Events: check for fully duplicate rows
    events_dups = events_df.duplicated().sum()
    dup_results['events_full_duplicates'] = events_dups
    logger.info(f"Events: {events_dups} fully duplicate rows")
    
    # Users: check for duplicate ids
    users_dups = users_df['id'].duplicated().sum()
    dup_results['users_duplicate_ids'] = users_dups
    logger.info(f"Users: {users_dups} duplicate ids")
    
    # Products: check for duplicate product_ids
    products_dups = products_df['product_id'].duplicated().sum()
    dup_results['products_duplicate_ids'] = products_dups
    logger.info(f"Products: {products_dups} duplicate product_ids")
    
    return dup_results

def profile_schema_issues(events_df, users_df):
    # Check schema and data type issues
    schema_results = {}
    
    # Check event_type contains only valid values
    # Note: using the event types that were actually generated in the data
    valid_event_types = ['page_view', 'click', 'purchase', 'add_to_cart', 'search', 'login', 'logout', 'signup']
    invalid_events = ~events_df['event_type'].isin(valid_event_types)
    invalid_event_count = invalid_events.sum()
    schema_results['invalid_event_type_count'] = invalid_event_count
    if invalid_event_count > 0:
        logger.info(f"Events: {invalid_event_count} rows with invalid event_type")
        logger.info(f"Invalid event types found: {events_df[invalid_events]['event_type'].unique()}")
    
    # Check that price is numeric
    if not pd.api.types.is_numeric_dtype(events_df['price']):
        schema_results['price_not_numeric'] = True
        logger.warning("Events: price column is not numeric")
    else:
        schema_results['price_not_numeric'] = False
    
    # Check that age is numeric
    if not pd.api.types.is_numeric_dtype(users_df['age']):
        schema_results['age_not_numeric'] = True
        logger.warning("Users: age column is not numeric")
    else:
        schema_results['age_not_numeric'] = False
    
    return schema_results

def profile_range_issues(events_df, users_df):
    # Check range and format issues
    range_results = {}
    
    # Check price > 0
    invalid_price = (events_df['price'] <= 0).sum()
    range_results['invalid_price_count'] = invalid_price
    logger.info(f"Events: {invalid_price} rows with price <= 0")
    
    # Check age between 0 and 100
    invalid_age = ((users_df['age'] < 0) | (users_df['age'] > 100)).sum()
    range_results['invalid_age_count'] = invalid_age
    logger.info(f"Users: {invalid_age} rows with age outside 0-100 range")
    
    # Check event_time not in future
    current_date = datetime.now()
    future_events = (pd.to_datetime(events_df['event_time']) > current_date).sum()
    range_results['future_event_count'] = future_events
    logger.info(f"Events: {future_events} rows with future event_time")
    
    # Check user_session not empty
    empty_session = (events_df['user_session'].isna() | (events_df['user_session'] == '')).sum()
    range_results['empty_session_count'] = empty_session
    logger.info(f"Events: {empty_session} rows with empty user_session")
    
    return range_results

def clean_events(events_df, schema_results, range_results):
    # Clean events data by dropping rows that fail validation checks
    logger.info("Starting events data cleaning")
    initial_count = len(events_df)
    
    # Drop rows with invalid event_type
    valid_event_types = ['page_view', 'click', 'purchase', 'add_to_cart', 'search', 'login', 'logout', 'signup']
    events_df = events_df[events_df['event_type'].isin(valid_event_types)]
    dropped_invalid_type = initial_count - len(events_df)
    logger.info(f"Dropped {dropped_invalid_type} rows with invalid event_type")
    
    # Drop rows with price <= 0
    before_price = len(events_df)
    events_df = events_df[events_df['price'] > 0]
    dropped_price = before_price - len(events_df)
    logger.info(f"Dropped {dropped_price} rows with price <= 0")
    
    # Drop rows with future event_time
    current_date = datetime.now()
    before_time = len(events_df)
    events_df = events_df[pd.to_datetime(events_df['event_time']) <= current_date]
    dropped_time = before_time - len(events_df)
    logger.info(f"Dropped {dropped_time} rows with future event_time")
    
    # Drop rows with empty user_session
    before_session = len(events_df)
    events_df = events_df[~(events_df['user_session'].isna() | (events_df['user_session'] == ''))]
    dropped_session = before_session - len(events_df)
    logger.info(f"Dropped {dropped_session} rows with empty user_session")
    
    # Drop fully duplicate rows
    before_dups = len(events_df)
    events_df = events_df.drop_duplicates()
    dropped_dups = before_dups - len(events_df)
    logger.info(f"Dropped {dropped_dups} duplicate rows")
    
    # Remove partitioning columns (year, month, day) that were added during storage
    if 'year' in events_df.columns:
        events_df = events_df.drop(columns=['year', 'month', 'day'])
        logger.info("Removed partitioning columns (year, month, day)")
    
    total_dropped = initial_count - len(events_df)
    logger.info(f"Events cleaning complete: kept {len(events_df)} rows, dropped {total_dropped} rows total")
    
    return events_df

def clean_users(users_df):
    # Clean users data
    logger.info("Starting users data cleaning")
    initial_count = len(users_df)
    
    # Drop rows with missing id
    users_df = users_df[users_df['id'].notna()]
    dropped_missing_id = initial_count - len(users_df)
    logger.info(f"Dropped {dropped_missing_id} rows with missing id")
    
    # Drop rows with invalid age (outside 0-100)
    before_age = len(users_df)
    users_df = users_df[(users_df['age'] >= 0) & (users_df['age'] <= 100)]
    dropped_age = before_age - len(users_df)
    logger.info(f"Dropped {dropped_age} rows with invalid age")
    
    # Fill missing city and gender with "unknown" (optional fields)
    # City is nested in address dict, so extract it first
    if 'address' in users_df.columns and users_df['address'].notna().any():
        users_df['city'] = users_df['address'].apply(lambda x: x.get('city') if isinstance(x, dict) else 'unknown')
    else:
        users_df['city'] = 'unknown'
    
    users_df['gender'] = users_df['gender'].fillna('unknown')
    logger.info("Filled missing city and gender values with 'unknown'")
    
    total_dropped = initial_count - len(users_df)
    logger.info(f"Users cleaning complete: kept {len(users_df)} rows, dropped {total_dropped} rows total")
    
    return users_df

def clean_products(products_df):
    # Clean products data - just drop duplicates
    logger.info("Starting products data cleaning")
    initial_count = len(products_df)
    
    # Drop any duplicate product_ids (shouldn't happen after grouping, but just in case)
    products_df = products_df.drop_duplicates(subset=['product_id'])
    dropped = initial_count - len(products_df)
    logger.info(f"Dropped {dropped} duplicate product_ids")
    
    logger.info(f"Products cleaning complete: kept {len(products_df)} rows")
    
    return products_df

def save_validated_data(events_df, products_df, users_df):
    # Save validated data to CSV files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'validated')
    os.makedirs(output_dir, exist_ok=True)
    
    # Save events
    events_path = os.path.join(output_dir, 'clickstream_validated.csv')
    events_df.to_csv(events_path, index=False)
    logger.info(f"Saved validated events to {events_path}")
    
    # Save products
    products_path = os.path.join(output_dir, 'products_validated.csv')
    products_df.to_csv(products_path, index=False)
    logger.info(f"Saved validated products to {products_path}")
    
    # Save users
    users_path = os.path.join(output_dir, 'users_validated.csv')
    users_df.to_csv(users_path, index=False)
    logger.info(f"Saved validated users to {users_path}")

def main():
    # Main validation function
    logger.info("=" * 60)
    logger.info("Starting data validation and profiling")
    logger.info("=" * 60)
    
    # Load data
    logger.info("Loading data from parquet partitions")
    events_df = load_events()
    users_df = load_users()
    
    if events_df is None or users_df is None:
        logger.error("Failed to load required data, exiting")
        return
    
    # Build products table
    products_df = build_products(events_df)
    
    # Run profiling checks
    logger.info("Running profiling checks")
    
    # Missing values
    logger.info("Checking for missing values")
    events_missing = profile_missing_values(events_df, 'Events')
    users_missing = profile_missing_values(users_df, 'Users')
    products_missing = profile_missing_values(products_df, 'Products')
    
    # Duplicates
    logger.info("Checking for duplicates")
    dup_results = profile_duplicates(events_df, users_df, products_df)
    
    # Schema issues
    logger.info("Checking for schema issues")
    schema_results = profile_schema_issues(events_df, users_df)
    
    # Range issues
    logger.info("Checking for range and format issues")
    range_results = profile_range_issues(events_df, users_df)
    
    # Clean data
    logger.info("Cleaning data")
    events_clean = clean_events(events_df, schema_results, range_results)
    users_clean = clean_users(users_df)
    products_clean = clean_products(products_df)
    
    # Save validated data
    logger.info("Saving validated data")
    save_validated_data(events_clean, products_clean, users_clean)
    
    # Compile profiling results for report
    profiling_results = {
        'missing_values': {
            'events': events_missing,
            'users': users_missing,
            'products': products_missing
        },
        'duplicates': dup_results,
        'schema_issues': schema_results,
        'range_issues': range_results,
        'row_counts': {
            'events_original': len(events_df),
            'events_cleaned': len(events_clean),
            'users_original': len(users_df),
            'users_cleaned': len(users_clean),
            'products': len(products_clean)
        }
    }
    
    # Print summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Events: {len(events_df)} -> {len(events_clean)} rows")
    logger.info(f"Users: {len(users_df)} -> {len(users_clean)} rows")
    logger.info(f"Products: {len(products_clean)} rows")
    logger.info("=" * 60)
    
    # Save profiling results to JSON for report generation
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_path = os.path.join(base_dir, 'reports', 'validation_results.json')
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(profiling_results, f, indent=2, default=str)
    
    logger.info(f"Saved profiling results to {results_path}")
    
    logger.info("Data validation completed successfully")
    
    return profiling_results

if __name__ == "__main__":
    results = main()
