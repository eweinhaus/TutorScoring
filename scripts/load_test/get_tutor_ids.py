#!/usr/bin/env python3
"""
Get tutor IDs from database for load testing.

This script queries the database to get valid tutor IDs that can be used
in the K6 load test script.

Usage:
    python scripts/load_test/get_tutor_ids.py --output tutor_ids.json
"""
import argparse
import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_dir)

from app.models.tutor import Tutor

# Load environment variables
load_dotenv(os.path.join(backend_dir, '.env'))


def main():
    parser = argparse.ArgumentParser(description='Get tutor IDs for load testing')
    parser.add_argument(
        '--output',
        type=str,
        default='tutor_ids.json',
        help='Output JSON file (default: tutor_ids.json)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum number of tutor IDs to fetch (default: 100)'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='Database URL (default: from DATABASE_URL env var)'
    )
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Connect to database
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Query tutors
        tutors = db.query(Tutor).filter(Tutor.is_active == True).limit(args.limit).all()
        
        tutor_ids = [str(tutor.id) for tutor in tutors]
        
        if not tutor_ids:
            print("Warning: No tutors found in database. You may need to generate test data first.")
            print("Run: python scripts/generate_data.py --tutors 100")
            sys.exit(1)
        
        # Save to JSON
        output_data = {
            'tutor_ids': tutor_ids,
            'count': len(tutor_ids),
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✅ Found {len(tutor_ids)} tutor IDs")
        print(f"✅ Saved to {args.output}")
        print(f"\nTo use in K6 script, update k6_session_load.js with these tutor IDs")
        
        # Also print as JavaScript array for easy copy-paste
        print("\nJavaScript array format:")
        print("const SAMPLE_TUTOR_IDS = [")
        for tutor_id in tutor_ids[:10]:  # Show first 10
            print(f"  '{tutor_id}',")
        if len(tutor_ids) > 10:
            print(f"  // ... and {len(tutor_ids) - 10} more")
        print("];")
        
    finally:
        db.close()


if __name__ == '__main__':
    main()


