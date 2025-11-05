#!/usr/bin/env python3
"""
Generate sample tutor data for testing.
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Tutor, Session, Reschedule


def generate_sample_data():
    """Generate sample data for testing."""
    print("🌱 Generating sample data...")
    
    # Get database connection from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_tutors = db.query(Tutor).count()
        if existing_tutors > 0:
            print(f"✅ Database already has {existing_tutors} tutors. Skipping seed.")
            return
        
        print("📝 Creating sample tutors...")
        
        # Create simple student IDs (sessions can use string IDs)
        student_ids = [f"student_{i+1}" for i in range(10)]
        print(f"✅ Using {len(student_ids)} student IDs")
        
        # Create sample tutors
        tutor_names = [
            "Alice Johnson", "Bob Smith", "Carol Williams", "David Brown",
            "Emma Davis", "Frank Miller", "Grace Wilson", "Henry Moore",
            "Iris Taylor", "Jack Anderson"
        ]
        
        tutors = []
        for i, name in enumerate(tutor_names):
            tutor = Tutor(
                name=name,
                email=f"{name.lower().replace(' ', '.')}@example.com",
                is_active=True
            )
            db.add(tutor)
            db.commit()
            db.refresh(tutor)
            tutors.append(tutor)
            print(f"  Created tutor: {name}")
        
        print(f"✅ Created {len(tutors)} tutors")
        
        # Create sessions and reschedules for each tutor
        print("📝 Creating sessions and reschedules...")
        
        for tutor in tutors:
            # Create 20-50 sessions per tutor
            num_sessions = random.randint(20, 50)
            reschedule_count = 0
            
            for j in range(num_sessions):
                # Random date in the last 90 days
                days_ago = random.randint(0, 90)
                scheduled_time = datetime.utcnow() - timedelta(days=days_ago)
                
                # Randomly decide if this session will be rescheduled (20% chance)
                will_reschedule = random.random() < 0.2
                
                session = Session(
                    tutor_id=tutor.id,
                    student_id=random.choice(student_ids),
                    scheduled_time=scheduled_time,
                    status="rescheduled" if will_reschedule else "completed",
                    duration_minutes=60
                )
                
                if not will_reschedule:
                    session.completed_time = scheduled_time + timedelta(minutes=60)
                
                db.add(session)
                db.commit()
                db.refresh(session)
                
                # Create reschedule if applicable
                if will_reschedule:
                    # Random hours before session (1-72 hours)
                    hours_before = Decimal(str(random.uniform(1.0, 72.0)))
                    cancelled_at = scheduled_time - timedelta(hours=float(hours_before))
                    
                    # Random new time (1-7 days later)
                    new_time = scheduled_time + timedelta(days=random.randint(1, 7))
                    
                    # Random initiator and reason
                    initiator = random.choice(["tutor", "student"])
                    reason_codes = ["personal", "sick", "emergency", "technical", "other"]
                    reason_code = random.choice(reason_codes)
                    
                    reasons = {
                        "personal": "Personal conflict",
                        "sick": "Feeling unwell",
                        "emergency": "Family emergency",
                        "technical": "Technical issues",
                        "other": "Other reason"
                    }
                    
                    reschedule = Reschedule(
                        session_id=session.id,
                        initiator=initiator,
                        original_time=scheduled_time,
                        new_time=new_time,
                        reason=reasons[reason_code],
                        reason_code=reason_code,
                        cancelled_at=cancelled_at,
                        hours_before_session=hours_before
                    )
                    
                    db.add(reschedule)
                    reschedule_count += 1
            
            db.commit()
            print(f"  {tutor.name}: {num_sessions} sessions ({reschedule_count} reschedules)")
        
        print("")
        print("✅ Sample data generated successfully!")
        print(f"   Tutors: {len(tutors)}")
        print(f"   Student IDs: {len(student_ids)}")
        
        # Get total sessions and reschedules
        total_sessions = db.query(Session).count()
        total_reschedules = db.query(Reschedule).count()
        
        print(f"   Sessions: {total_sessions}")
        print(f"   Reschedules: {total_reschedules}")
        
    except Exception as e:
        print(f"❌ Error generating data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    generate_sample_data()

