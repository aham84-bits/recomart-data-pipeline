# Schedules and orchestrates data ingestion tasks
# In a real deployment, this would be replaced by an Airflow DAG,
# but for this assignment we're using the schedule library to keep it simple to run locally.
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import schedule
import time
from ingestion.logger_config import get_logger
from ingestion.api_ingest import fetch_users
from ingestion.csv_ingest import load_events

logger = get_logger(__name__)

def log_next_runs():
    # Log the next scheduled run time for all jobs
    for job in schedule.jobs:
        logger.info(f"Next run for {job.job_func.__name__}: {job.next_run}")

def run_api_ingestion():
    # Run the API ingestion job with error handling
    try:
        logger.info("Starting API ingestion job")
        fetch_users()
        logger.info("API ingestion job finished successfully")
    except Exception as e:
        logger.error(f"API ingestion job failed: {str(e)}")

def run_csv_ingestion():
    # Run the CSV ingestion job with error handling
    try:
        logger.info("Starting CSV ingestion job")
        load_events()
        logger.info("CSV ingestion job finished successfully")
    except Exception as e:
        logger.error(f"CSV ingestion job failed: {str(e)}")

def main():
    # Set up the scheduled jobs
    
    # Run API ingestion every 5 minutes
    schedule.every(5).minutes.do(run_api_ingestion)
    logger.info("Scheduled API ingestion to run every 5 minutes")
    
    # Run CSV ingestion once a day at 5:50 PM
    schedule.every().day.at("18:10").do(run_csv_ingestion)
    logger.info("Scheduled CSV ingestion to run daily at 5:50 PM")
    
    # Log initial next run times
    log_next_runs()
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
