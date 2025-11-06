"""
Script to populate upcoming sessions for testing the reschedule prediction dashboard.
Creates sessions with future scheduled times and generates predictions for them.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
import random

# Add backend to path
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
from app.models.tutor import Tutor
from app.utils.database import SessionLocal
from app.services.tutor_service import get_tutor_statistics
from app.services.reschedule_prediction_service import get_or_create_prediction
from app.schemas.session import SessionCreate

def get_random_tutors(db: Session, count: int = 10) -> list:
    """Get random tutors from database."""
    tutors = db.query(Tutor).limit(count).all()
    if not tutors:
        raise ValueError("No tutors found in database. Please create tutors first.")
    return tutors

def generate_upcoming_session(tutor_id: str, days_ahead: int = None, duration_variation: str = "normal") -> dict:
    """Generate a session with future scheduled time.
    
    Args:
        tutor_id: Tutor ID
        days_ahead: Days in the future (None = random 1-30)
        duration_variation: 'short', 'normal', or 'long' to vary durations (affects risk)
    """
    if days_ahead is None:
        days_ahead = random.randint(1, 14)  # Random 1-14 days ahead for better visibility
    
    now = datetime.utcnow()
    scheduled_time = now + timedelta(days=days_ahead, hours=random.randint(9, 20))
    
    # Random student ID
    student_id = f"student-{random.randint(1000, 9999)}"
    
    # Vary duration to create different risk profiles
    # Longer sessions might have higher reschedule risk
    if duration_variation == "short":
        duration_minutes = random.choice([30, 45])
    elif duration_variation == "long":
        duration_minutes = random.choice([75, 90])
    else:
        duration_minutes = random.choice([45, 60, 75])
    
    return {
        "session_id": str(uuid4()),
        "tutor_id": tutor_id,
        "student_id": student_id,
        "scheduled_time": scheduled_time.isoformat(),
        "status": "no_show",  # Use 'no_show' for upcoming sessions (not yet completed)
        "duration_minutes": duration_minutes,
        "completed_time": None,  # Must be None for 'no_show' status
    }

def create_upcoming_sessions(db: Session, num_sessions: int = 20):
    """Create upcoming sessions with predictions."""
    print(f"Creating {num_sessions} upcoming sessions...")
    
    # Get tutors
    tutors = get_random_tutors(db, count=min(10, num_sessions))
    print(f"Found {len(tutors)} tutors")
    
    created_count = 0
    prediction_count = 0
    
    for i in range(num_sessions):
        try:
            # Select random tutor
            tutor = random.choice(tutors)
            
            # Generate session data
            # Vary days ahead to create variety (some soon, some later)
            days_ahead = random.randint(1, 7) if i % 3 == 0 else random.randint(8, 14)
            
            # Vary duration to create different risk profiles
            duration_variation = random.choice(["short", "normal", "long"])
            
            session_data = generate_upcoming_session(str(tutor.id), days_ahead, duration_variation)
            
            # Create session using the service
            session_create = SessionCreate(**session_data)
            from app.services.session_service import create_session
            session = create_session(session_create, db)
            
            # Generate prediction
            try:
                tutor_stats = get_tutor_statistics(str(tutor.id), db)
                prediction = get_or_create_prediction(session, tutor_stats, db)
                prediction_count += 1
                
                if (i + 1) % 5 == 0:
                    print(f"  Created {i + 1}/{num_sessions} sessions... (predictions: {prediction_count})")
            except Exception as e:
                print(f"  Warning: Failed to generate prediction for session {session.id}: {e}")
            
            created_count += 1
            
        except Exception as e:
            print(f"  Error creating session {i + 1}: {e}")
            continue
    
    db.commit()
    print(f"\n✅ Created {created_count} upcoming sessions")
    print(f"✅ Generated {prediction_count} predictions")
    return created_count, prediction_count

def main():
    """Main function."""
    print("=" * 60)
    print("Populate Upcoming Sessions")
    print("=" * 60)
    
    num_sessions = int(os.getenv("NUM_SESSIONS", 30))
    
    db = SessionLocal()
    try:
        create_upcoming_sessions(db, num_sessions)
        
        # Show summary
        now = datetime.utcnow()
        end_date = now + timedelta(days=30)
        upcoming_count = db.query(SessionModel).filter(
            SessionModel.scheduled_time >= now,
            SessionModel.scheduled_time <= end_date,
            SessionModel.status != 'completed'
        ).count()
        
        print(f"\n📊 Summary:")
        print(f"   Total upcoming sessions (next 30 days): {upcoming_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

