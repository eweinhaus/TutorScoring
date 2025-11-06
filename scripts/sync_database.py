#!/usr/bin/env python3
"""
Script to sync local database to production database.
Can be run locally or via ECS task.
"""
import os
import sys
import argparse
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import boto3
from urllib.parse import urlparse

def get_table_names(engine):
    """Get all table names from database."""
    inspector = inspect(engine)
    return inspector.get_table_names()

def sync_table(local_session, prod_session, table_name):
    """Sync a single table from local to production."""
    print(f"  Syncing {table_name}...")
    
    # Get table class dynamically
    from sqlalchemy import Table, MetaData
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=prod_session.bind)
    
    # Delete all existing data
    prod_session.execute(table.delete())
    prod_session.commit()
    
    # Read all data from local
    local_result = local_session.execute(f"SELECT * FROM {table_name}")
    rows = local_result.fetchall()
    
    if not rows:
        print(f"    No data to sync")
        return 0
    
    # Insert data into production
    columns = [col.name for col in table.columns]
    insert_stmt = table.insert()
    
    data_to_insert = []
    for row in rows:
        row_dict = dict(row._mapping)
        # Filter to only columns that exist in table
        filtered_row = {k: v for k, v in row_dict.items() if k in columns}
        data_to_insert.append(filtered_row)
    
    if data_to_insert:
        prod_session.execute(insert_stmt, data_to_insert)
        prod_session.commit()
        print(f"    Synced {len(data_to_insert)} rows")
        return len(data_to_insert)
    
    return 0

def main():
    parser = argparse.ArgumentParser(description='Sync local database to production')
    parser.add_argument('--local-url', help='Local database URL')
    parser.add_argument('--prod-url', help='Production database URL')
    parser.add_argument('--s3-bucket', help='S3 bucket for dump file')
    parser.add_argument('--s3-key', help='S3 key for dump file')
    parser.add_argument('--mode', choices=['direct', 's3'], default='direct',
                       help='Sync mode: direct or via S3')
    
    args = parser.parse_args()
    
    # Get database URLs
    if args.mode == 's3':
        # Running in ECS - download prod URL from S3 and get local dump
        if not all([args.s3_bucket, args.s3_key, args.prod_url]):
            print("❌ S3 mode requires --s3-bucket, --s3-key, and --prod-url")
            sys.exit(1)
        
        # Download dump from S3
        s3 = boto3.client('s3')
        dump_file = '/tmp/local_dump.sql'
        print(f"📥 Downloading s3://{args.s3_bucket}/{args.s3_key}...")
        s3.download_file(args.s3_bucket, args.s3_key, dump_file)
        print("✅ Download complete")
        
        # Import dump to production
        import subprocess
        print("📥 Importing dump to production...")
        result = subprocess.run(
            ['psql', args.prod_url, '-f', dump_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Import failed: {result.stderr}")
            sys.exit(1)
        
        print("✅ Import complete")
        return
    
    # Direct mode - sync using SQLAlchemy
    if not args.local_url or not args.prod_url:
        print("❌ Direct mode requires --local-url and --prod-url")
        sys.exit(1)
    
    print("🔷 Connecting to databases...")
    local_engine = create_engine(args.local_url)
    prod_engine = create_engine(args.prod_url)
    
    LocalSession = sessionmaker(bind=local_engine)
    ProdSession = sessionmaker(bind=prod_engine)
    
    local_session = LocalSession()
    prod_session = ProdSession()
    
    try:
        print("✅ Connected")
        print("")
        print("🔷 Getting table list...")
        tables = get_table_names(local_engine)
        print(f"✅ Found {len(tables)} tables")
        print("")
        
        print("🔷 Syncing tables...")
        total_rows = 0
        for table in tables:
            if table.startswith('alembic_'):
                continue  # Skip alembic version table
            try:
                rows = sync_table(local_session, prod_session, table)
                total_rows += rows
            except Exception as e:
                print(f"    ⚠️  Error syncing {table}: {e}")
        
        print("")
        print(f"✅ Sync complete! Total rows synced: {total_rows}")
        
    finally:
        local_session.close()
        prod_session.close()

if __name__ == '__main__':
    main()

