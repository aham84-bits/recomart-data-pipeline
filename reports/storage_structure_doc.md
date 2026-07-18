# Storage Structure for RecoMart Pipeline

So this is how the storage layout works after running the upload script.

## Folder Structure

Here's what storage/raw/ looks like after the script runs:

```
storage/raw/
├── events/
│   ├── year=2024/
│   │   ├── month=01/
│   │   │   ├── day=15/
│   │   │   │   └── events.parquet
│   │   │   └── day=16/
│   │   │   │   └── events.parquet
│   │   └── month=02/
│   │       └── day=01/
│   │           └── events.parquet
│   └── year=2026/
│       └── month=07/
│           └── day=18/
│               └── events.parquet
└── users/
    └── snapshot_date=2026-07-18/
        └── users.parquet
```

## Why I partitioned events by date

Events are basically time-series data that keeps growing, so I split them by year/month/day. The main reason is that it makes it way faster to grab just the data you need. Like if feature engineering only wants the last week of data, it can just read those 7 folders instead of scanning everything. Also if something goes wrong with one day's data, we can just reprocess that one day instead of redoing the whole thing.

## Why users data is just a snapshot folder

Users data is different - it's a small reference table that gets refreshed all at once, not like events which keep growing. So instead of partitioning by date, I just put it in a snapshot folder with today's date (snapshot_date=YYYY-MM-DD). This way we know which version we're using, and when we update it we just make a new snapshot folder.

## Why I used parquet instead of csv

I went with parquet instead of csv because:
- It's columnar so reading specific columns is faster
- Files are smaller since they're compressed
- Data types stay as they are (no more parsing strings to ints/dates)
- For feature engineering which will query this a lot, parquet is just more efficient

## What happens if a partition already exists

If the script runs again and a partition folder is already there, it just logs a warning and skips it instead of overwriting. This way we don't accidentally lose data if we run the script multiple times. If you need to reprocess something, just delete that folder first and run it again.
