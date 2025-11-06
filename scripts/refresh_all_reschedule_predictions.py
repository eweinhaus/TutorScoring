#!/usr/bin/env python3
"""
Refresh all reschedule predictions in the database.

This script:
1. Clears the model cache to ensure new model is loaded
2. Refreshes all reschedule predictions for upcoming sessions
3. Updates predictions with new model version

Run with: python scripts/refresh_all_reschedule_predictions.py
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from app.utils.database import SessionLocal
from app.services.reschedule_prediction_service import refresh_all_reschedule_predictions, clear_model_cache

def main():
    """Main function to refresh all reschedule predictions."""
    print("=" * 60)
    print("Refreshing All Reschedule Predictions")
    print("=" * 60)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Clear model cache to ensure new model is loaded
        print("\nClearing model cache...")
        clear_model_cache()
        print("✅ Model cache cleared")
        
        print("\nRefreshing all reschedule predictions for upcoming sessions...")
        total_refreshed = refresh_all_reschedule_predictions(db)
        
        print("\n" + "=" * 60)
        print(f"✅ Successfully refreshed {total_refreshed} reschedule predictions")
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

