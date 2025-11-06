#!/usr/bin/env python3
"""
Refresh all match predictions in the database.

This script calls the refresh_all_predictions function to update
all match predictions with the latest data.
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from app.utils.database import get_db
from app.services.match_prediction_service import refresh_all_predictions, clear_model_cache

def main():
    """Main function to refresh all predictions."""
    print("=" * 60)
    print("Refreshing All Match Predictions")
    print("=" * 60)
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Clear model cache to ensure new model is loaded
        print("\nClearing model cache...")
        clear_model_cache()
        print("✅ Model cache cleared")
        
        print("\nRefreshing all match predictions...")
        total_refreshed = refresh_all_predictions(db)
        
        print("\n" + "=" * 60)
        print(f"✅ Successfully refreshed {total_refreshed} match predictions")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()

