#!/usr/bin/env python3
"""
Database setup script for Tutor Quality Scoring System.

This script helps initialize the database with migrations and optionally seed data.

Usage:
    python scripts/setup_db.py --init
    python scripts/setup_db.py --init --seed-data
    python scripts/setup_db.py --clear
"""
import argparse
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv

# Load environment variables
load_dotenv(backend_dir / '.env')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")


def verify_db_connection() -> bool:
    """Verify database connection."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✓ Database connection verified")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def run_migrations() -> bool:
    """Run Alembic migrations."""
    try:
        print("Running database migrations...")
        alembic_cfg = Config(str(backend_dir / 'alembic.ini'))
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations applied successfully")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


def generate_data() -> bool:
    """Generate synthetic data."""
    try:
        print("Generating synthetic data...")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / 'generate_data.py'),
             '--tutors', '100', '--sessions', '3000', '--days', '90'],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Synthetic data generated successfully")
            return True
        else:
            print(f"✗ Data generation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Data generation failed: {e}")
        return False


def verify_setup() -> bool:
    """Verify database setup."""
    try:
        print("Verifying database setup...")
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['tutors', 'sessions', 'reschedules', 'tutor_scores', 'email_reports']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"✗ Missing tables: {missing_tables}")
            return False
        
        print("✓ All required tables exist")
        return True
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False


def clear_data() -> bool:
    """Clear all data from database."""
    try:
        print("Clearing all data...")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / 'generate_data.py'),
             '--tutors', '0', '--sessions', '0', '--days', '0', '--clear-existing'],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Data cleared successfully")
            return True
        else:
            print(f"✗ Data clearing failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Data clearing failed: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Setup database for Tutor Quality Scoring System')
    parser.add_argument('--init', action='store_true', help='Initialize database with migrations')
    parser.add_argument('--seed-data', action='store_true', help='Generate synthetic data after initialization')
    parser.add_argument('--clear', action='store_true', help='Clear all existing data')
    
    args = parser.parse_args()
    
    if not any([args.init, args.seed_data, args.clear]):
        parser.print_help()
        sys.exit(1)
    
    # Verify database connection
    if not verify_db_connection():
        sys.exit(1)
    
    success = True
    
    # Clear data if requested
    if args.clear:
        success = clear_data() and success
    
    # Initialize database
    if args.init:
        success = run_migrations() and success
        if success:
            success = verify_setup() and success
        
        # Generate seed data if requested
        if args.seed_data and success:
            success = generate_data() and success
    
    if success:
        print("\n✓ Database setup completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Database setup failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()

