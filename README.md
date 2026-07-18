# RecoMart Data Ingestion Module

This module ingests data from two sources for the RecoMart project:
- CSV file (REES46 e-commerce events)
- REST API (DummyJSON user profiles)

## Files

- **logger_config.py** - Sets up logging to both file and console with rotation
- **csv_ingest.py** - Reads and cleans the events CSV file in chunks
- **api_ingest.py** - Fetches user data from DummyJSON API with retry logic
- **scheduler.py** - Runs the ingestion jobs on a schedule
- **main.py** - Main entry point for the module

## How to Run

1. Install dependencies:
   `
   pip install -r requirements.txt
   `

2. Run the scheduler:
   `
   python ingestion/scheduler.py
   `

Or run individual scripts:
   `
   python ingestion/csv_ingest.py
   python ingestion/api_ingest.py
   `

## Output Locations

- **Logs**: logs/ingestion.log (rotates at 2MB, keeps 3 backups)
- **Cleaned events**: data/raw/events_clean.csv
- **User data**: data/raw/users.json

## Scheduling Settings

- **API ingestion**: Every 15 minutes (simulates near real-time updates)
- **CSV ingestion**: Daily at 2:00 AM (simulates batch load)

## Retry Settings

- **API requests**: Up to 3 retries with 2-second delay between attempts
- If all retries fail for a page, it logs an error and continues to the next page
- CSV ingestion has error handling but no retry (file read errors are logged)

## Data Cleaning

The CSV ingestion removes:
- Rows with missing or invalid price (price <= 0)
- Rows with future dates in event_time
- Exact duplicate rows

## Notes

- In a real deployment, the scheduler would be replaced by an Airflow DAG
- The CSV file should be placed at data/raw/events.csv before running
- The scheduler runs continuously until stopped with Ctrl+C
