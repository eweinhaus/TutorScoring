#!/usr/bin/env python3
"""
Synthetic data generator for Tutor Quality Scoring System.

Generates realistic test data including:
- Tutors with varied risk profiles
- Sessions with realistic temporal patterns
- Reschedules with correlated patterns
- Tutor scores calculated from actual data

Usage:
    python scripts/generate_data.py --tutors 100 --sessions 3000 --days 90 --clear-existing
"""
import argparse
import sys
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import random
from faker import Faker

# Add backend directory to path to import app models
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

from app.models import (
    Tutor, Session, Reschedule, TutorScore, EmailReport
)

# Load environment variables from backend/.env
load_dotenv(os.path.join(backend_dir, '.env'))

# Initialize Faker with multiple locales for more realistic names
fake = Faker(['en_US', 'en_GB', 'en_CA', 'en_AU'])
# Set seed for reproducibility (but different each run)
fake.seed_instance(random.randint(0, 999999))

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# Configuration constants
RISK_DISTRIBUTION = {
    'low': 0.70,      # 0-10% reschedule rate (70% low risk)
    'medium': 0.20,   # 10-20% reschedule rate (20% warning/medium risk)
    'high': 0.10      # >20% reschedule rate (10% high risk)
}

SESSION_STATUS_DISTRIBUTION = {
    'completed': 0.70,
    'rescheduled': 0.25,
    'no_show': 0.05
}

RESCHEDULE_INITIATOR_DISTRIBUTION = {
    'tutor': 0.982,
    'student': 0.018
}

RESCHEDULE_TIMING_DISTRIBUTION = {
    'last_minute': 0.40,  # <24 hours
    'planned': 0.60       # >24 hours
}

RESCHEDULE_REASONS = [
    ('Personal emergency', 'personal'),
    ('Scheduling conflict', 'scheduling'),
    ('Family issue', 'family'),
    ('Technical issues', 'technical'),
    ('Health concern', 'health'),
    ('Work commitment', 'work'),
    ('Transportation issue', 'transportation'),
    ('Childcare conflict', 'childcare'),
    ('Weather-related', 'weather'),
    ('Student requested', 'student_request'),
]

RISK_THRESHOLD = Decimal('15.00')


def choose_weighted(options: Dict[str, float]) -> str:
    """Choose an option based on weighted distribution."""
    r = random.random()
    cumulative = 0.0
    for option, weight in options.items():
        cumulative += weight
        if r <= cumulative:
            return option
    return list(options.keys())[-1]


def generate_email_from_name(name: str) -> str:
    """
    Generate a realistic email address from a tutor's name.
    
    Examples:
        "John Smith" -> "john.smith@tutoring.com"
        "Sarah Johnson" -> "sarah.johnson@tutoring.com"
        "Michael O'Brien" -> "michael.obrien@tutoring.com"
    """
    # Normalize name: lowercase, remove apostrophes, replace spaces/hyphens with dots
    normalized = name.lower()
    normalized = normalized.replace("'", "").replace("'", "")
    normalized = normalized.replace("-", ".").replace(" ", ".")
    # Remove any double dots
    while ".." in normalized:
        normalized = normalized.replace("..", ".")
    
    # Email domains that look realistic
    domains = [
        'tutoring.com',
        'teachonline.com',
        'educonnect.com',
        'tutorhub.com',
        'learnwith.me',
        'gmail.com',  # Some use personal email
        'yahoo.com',
        'outlook.com'
    ]
    
    # 80% use professional domains, 20% personal
    if random.random() < 0.80:
        domain = random.choice(domains[:5])
    else:
        domain = random.choice(domains[5:])
    
    return f"{normalized}@{domain}"


def generate_tutors(db: SessionLocal, count: int, start_date: datetime) -> List[Tutor]:
    """
    Generate tutor data with varied risk profiles and realistic names/emails.
    
    Args:
        db: Database session
        count: Number of tutors to generate
        start_date: Start date for creation dates
        
    Returns:
        List of created Tutor objects
    """
    tutors = []
    risk_categories = []
    used_names = set()  # Track names to avoid exact duplicates
    used_emails = set()  # Track emails to avoid duplicates
    
    # Assign risk categories based on distribution
    for i in range(count):
        risk_cat = choose_weighted(RISK_DISTRIBUTION)
        risk_categories.append(risk_cat)
    
    print(f"Generating {count} tutors with realistic names and emails...")
    for i in range(count):
        # Creation date varied over past 6 months
        days_ago = random.randint(0, 180)
        created_at = start_date - timedelta(days=days_ago)
        
        # Generate unique name without titles (avoid "Mr", "Dr", etc.)
        max_attempts = 50
        name = None
        for _ in range(max_attempts):
            # Use first_name + last_name to avoid titles like "Mr", "Dr", etc.
            candidate = f"{fake.first_name()} {fake.last_name()}"
            if candidate not in used_names:
                name = candidate
                used_names.add(name)
                break
        
        if name is None:
            # Fallback: add suffix to make unique
            name = f"{fake.first_name()} {fake.last_name()} {random.randint(1, 999)}"
            used_names.add(name)
        
        # Generate matching email (90% have email, 10% don't)
        email = None
        if random.random() < 0.90:
            max_email_attempts = 50
            for _ in range(max_email_attempts):
                candidate_email = generate_email_from_name(name)
                if candidate_email not in used_emails:
                    email = candidate_email
                    used_emails.add(email)
                    break
            
            if email is None:
                # Fallback: add number to make unique
                base_email = generate_email_from_name(name)
                username, domain = base_email.split('@')
                email = f"{username}{random.randint(1, 999)}@{domain}"
                used_emails.add(email)
        
        tutor = Tutor(
            name=name,
            email=email,
            is_active=random.random() < 0.90,  # 90% active
            created_at=created_at,
            updated_at=created_at
        )
        
        tutors.append(tutor)
        db.add(tutor)
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{count} tutors...")
            db.flush()
    
    db.commit()
    print(f"✓ Created {len(tutors)} tutors with unique names and matching emails")
    
    # Store risk category for later use
    for tutor, risk_cat in zip(tutors, risk_categories):
        tutor._risk_category = risk_cat
    
    return tutors


def generate_sessions(db: SessionLocal, tutors: List[Tutor], count: int, days: int) -> List[Session]:
    """
    Generate session data with realistic temporal patterns.
    
    Args:
        db: Database session
        tutors: List of tutors
        count: Number of sessions to generate
        days: Number of days to generate sessions over
        
    Returns:
        List of created Session objects
    """
    sessions = []
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Calculate session frequency per tutor based on risk category
    tutor_session_counts = {}
    for tutor in tutors:
        risk_cat = getattr(tutor, '_risk_category', 'low')
        if risk_cat == 'high':
            # High-risk tutors: 3-5 sessions per week
            base_freq = random.uniform(3, 5) / 7
        elif risk_cat == 'medium':
            # Medium-risk tutors: 1.5-3 sessions per week
            base_freq = random.uniform(1.5, 3) / 7
        else:
            # Low-risk tutors: 1-2 sessions per week
            base_freq = random.uniform(1, 2) / 7
        tutor_session_counts[tutor.id] = base_freq
    
    # Total sessions per tutor
    total_days = days
    total_sessions_by_tutor = {}
    remaining_sessions = count
    
    for tutor in tutors:
        freq = tutor_session_counts[tutor.id]
        expected = int(freq * total_days)
        actual = min(expected, remaining_sessions // len(tutors) + random.randint(-2, 2))
        actual = max(1, actual)  # At least 1 session
        total_sessions_by_tutor[tutor.id] = actual
        remaining_sessions -= actual
    
    # Distribute remaining sessions
    for _ in range(remaining_sessions):
        tutor = random.choice(tutors)
        total_sessions_by_tutor[tutor.id] += 1
    
    print(f"Generating {count} sessions over {days} days...")
    session_idx = 0
    
    for tutor in tutors:
        tutor_sessions_count = total_sessions_by_tutor.get(tutor.id, 0)
        
        # Generate dates evenly distributed across the time period
        # Create a list of potential dates for this tutor's sessions
        date_offsets = []
        if tutor_sessions_count > 0:
            if tutor_sessions_count == 1:
                # Single session - place it randomly
                date_offsets = [random.randint(0, days - 1)]
            else:
                # Multiple sessions - spread them evenly
                # Use a combination of evenly spaced and random dates
                for i in range(tutor_sessions_count):
                    # Mix of evenly spaced (70%) and random (30%) for natural variation
                    if random.random() < 0.70:
                        # Evenly spaced across the period
                        offset = int((i / max(1, tutor_sessions_count - 1)) * (days - 1))
                        # Add some jitter (±2 days) to avoid exact spacing
                        offset += random.randint(-2, 2)
                        offset = max(0, min(days - 1, offset))  # Clamp to valid range
                    else:
                        # Random placement
                        offset = random.randint(0, days - 1)
                    date_offsets.append(offset)
            
            # Sort dates to ensure chronological order
            date_offsets.sort()
        
        for session_num in range(tutor_sessions_count):
            # Get the date offset for this session
            day_offset = date_offsets[session_num]
            scheduled_date = start_date + timedelta(days=day_offset)
            
            # Ensure date is within bounds (should be, but double-check)
            if scheduled_date < start_date:
                scheduled_date = start_date
            if scheduled_date > end_date:
                scheduled_date = end_date
            
            # Peak hours: 3-8 PM (60% of sessions)
            if random.random() < 0.60:
                hour = random.randint(15, 19)  # 3-8 PM
            else:
                hour = random.randint(9, 21)  # 9 AM - 9 PM
            
            scheduled_time = scheduled_date.replace(
                hour=hour,
                minute=random.randint(0, 59),
                second=0,
                microsecond=0
            )
            
            # Generate status
            status = choose_weighted(SESSION_STATUS_DISTRIBUTION)
            
            # Generate student ID with realistic patterns
            # 60% unique students, 30% repeat customers, 10% frequent repeaters
            student_pool_size = max(100, int(count * 0.6))  # Pool of unique students
            if not hasattr(generate_sessions, '_student_ids'):
                # Initialize student ID pool with realistic identifiers
                generate_sessions._student_ids = []
                
                # Generate realistic student identifiers using multiple formats
                for j in range(student_pool_size):
                    # Use mix of realistic formats:
                    # 1. UUIDs (40% - most common in modern systems)
                    # 2. Email-based (30% - student emails)
                    # 3. Name-based codes (20% - firstname.lastname format)
                    # 4. Alphanumeric codes (10% - short codes)
                    format_choice = random.random()
                    
                    if format_choice < 0.40:
                        # UUID format (most realistic for modern platforms)
                        student_id = str(uuid.uuid4())
                    elif format_choice < 0.70:
                        # Email-based identifier
                        student_name = fake.first_name().lower()
                        last_name = fake.last_name().lower()
                        student_id = f"{student_name}.{last_name}@student.edu"
                    elif format_choice < 0.90:
                        # Name-based code (firstname.lastname.studentid)
                        first_name = fake.first_name().lower()
                        last_name = fake.last_name().lower()
                        student_num = random.randint(1000, 9999)
                        student_id = f"{first_name}.{last_name}.{student_num}"
                    else:
                        # Short alphanumeric code
                        letters = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=3))
                        numbers = random.randint(100000, 999999)
                        student_id = f"{letters}{numbers}"
                    
                    generate_sessions._student_ids.append(student_id)
                
                # Add some frequent repeaters (same format distribution)
                for _ in range(int(student_pool_size * 0.1)):
                    format_choice = random.random()
                    
                    if format_choice < 0.40:
                        student_id = str(uuid.uuid4())
                    elif format_choice < 0.70:
                        student_name = fake.first_name().lower()
                        last_name = fake.last_name().lower()
                        student_id = f"{student_name}.{last_name}@student.edu"
                    elif format_choice < 0.90:
                        first_name = fake.first_name().lower()
                        last_name = fake.last_name().lower()
                        student_num = random.randint(1000, 9999)
                        student_id = f"{first_name}.{last_name}.{student_num}"
                    else:
                        letters = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=3))
                        numbers = random.randint(100000, 999999)
                        student_id = f"{letters}{numbers}"
                    
                    generate_sessions._student_ids.append(student_id)
            
            rand = random.random()
            if rand < 0.60:
                # New student - pick from pool
                student_id = random.choice(generate_sessions._student_ids[:student_pool_size])
            elif rand < 0.90:
                # Repeat customer - pick from existing (weighted toward frequent repeaters)
                student_id = random.choice(generate_sessions._student_ids)
            else:
                # Frequent repeater - pick from last 10% of pool
                student_id = random.choice(generate_sessions._student_ids[-int(student_pool_size * 0.1):])
            
            completed_time = None
            duration_minutes = None
            
            if status == 'completed':
                # Completed sessions have completion time and duration
                completed_time = scheduled_time + timedelta(
                    minutes=random.randint(30, 120)
                )
                duration_minutes = int((completed_time - scheduled_time).total_seconds() / 60)
            
            session = Session(
                tutor_id=tutor.id,
                student_id=student_id,
                scheduled_time=scheduled_time,
                completed_time=completed_time,
                status=status,
                duration_minutes=duration_minutes,
                created_at=scheduled_time - timedelta(days=random.randint(1, 7)),
                updated_at=datetime.utcnow()
            )
            
            sessions.append(session)
            db.add(session)
            session_idx += 1
            
            if session_idx % 100 == 0:
                print(f"  Created {session_idx}/{count} sessions...")
                db.flush()
    
    db.commit()
    print(f"✓ Created {len(sessions)} sessions")
    
    return sessions


def generate_reschedules(db: SessionLocal, sessions: List[Session]) -> List[Reschedule]:
    """
    Generate reschedule data for rescheduled sessions.
    
    Args:
        db: Database session
        sessions: List of sessions (only rescheduled ones will have reschedules)
        
    Returns:
        List of created Reschedule objects
    """
    reschedules = []
    rescheduled_sessions = [s for s in sessions if s.status == 'rescheduled']
    
    print(f"Generating reschedules for {len(rescheduled_sessions)} sessions...")
    
    for session in rescheduled_sessions:
        # Initiator: 98.2% tutor, 1.8% student
        initiator = choose_weighted(RESCHEDULE_INITIATOR_DISTRIBUTION)
        
        # Timing: 40% last-minute, 60% planned
        timing = choose_weighted(RESCHEDULE_TIMING_DISTRIBUTION)
        
        if timing == 'last_minute':
            # <24 hours before
            hours_before = random.uniform(1, 24)
        else:
            # >24 hours before
            hours_before = random.uniform(24, 168)  # Up to 7 days
        
        cancelled_at = session.scheduled_time - timedelta(hours=hours_before)
        
        # Reason
        reason, reason_code = random.choice(RESCHEDULE_REASONS)
        
        # New time: 80% set (future), 20% NULL (cancelled)
        new_time = None
        if random.random() < 0.80:
            # Set new time (must be after original)
            new_time = session.scheduled_time + timedelta(
                days=random.randint(1, 14)
            )
        
        reschedule = Reschedule(
            session_id=session.id,
            initiator=initiator,
            original_time=session.scheduled_time,
            new_time=new_time,
            reason=reason,
            reason_code=reason_code,
            cancelled_at=cancelled_at,
            hours_before_session=Decimal(str(round(hours_before, 2))),
            created_at=cancelled_at
        )
        
        reschedules.append(reschedule)
        db.add(reschedule)
    
    db.commit()
    print(f"✓ Created {len(reschedules)} reschedules")
    
    return reschedules


def calculate_tutor_scores(db: SessionLocal, tutors: List[Tutor]) -> List[TutorScore]:
    """
    Calculate and create tutor scores based on actual session data.
    
    Args:
        db: Database session
        tutors: List of tutors
        
    Returns:
        List of created/updated TutorScore objects
    """
    from sqlalchemy import and_, func
    from datetime import datetime, timedelta
    
    print("Calculating tutor scores...")
    tutor_scores = []
    
    now = datetime.utcnow()
    windows = [
        (7, '7d'),
        (30, '30d'),
        (90, '90d')
    ]
    
    for tutor in tutors:
        scores = {}
        counts = {}
        reschedule_counts = {}
        
        for days, suffix in windows:
            cutoff_date = now - timedelta(days=days)
            
            # Get all sessions in window
            tutor_sessions = [
                s for s in tutor.sessions
                if s.scheduled_time >= cutoff_date
            ]
            
            total = len(tutor_sessions)
            counts[suffix] = total
            
            # Count tutor-initiated reschedules
            tutor_reschedules = len([
                s for s in tutor_sessions
                if s.status == 'rescheduled'
                and s.reschedule
                and s.reschedule.initiator == 'tutor'
            ])
            
            reschedule_counts[suffix] = tutor_reschedules
            
            # Calculate rate
            if total > 0:
                rate = (tutor_reschedules / total) * 100
                scores[suffix] = Decimal(str(round(rate, 2)))
            else:
                scores[suffix] = None
        
        # Check if high risk
        is_high_risk = (
            (scores.get('7d') or 0) > RISK_THRESHOLD or
            (scores.get('30d') or 0) > RISK_THRESHOLD or
            (scores.get('90d') or 0) > RISK_THRESHOLD
        )
        
        # Create or update TutorScore
        tutor_score = db.query(TutorScore).filter_by(tutor_id=tutor.id).first()
        
        if tutor_score:
            tutor_score.update_rates(
                scores['7d'], scores['30d'], scores['90d'],
                counts['7d'], counts['30d'], counts['90d'],
                reschedule_counts['7d'], reschedule_counts['30d'], reschedule_counts['90d']
            )
        else:
            tutor_score = TutorScore(
                tutor_id=tutor.id,
                reschedule_rate_7d=scores['7d'],
                reschedule_rate_30d=scores['30d'],
                reschedule_rate_90d=scores['90d'],
                total_sessions_7d=counts['7d'],
                total_sessions_30d=counts['30d'],
                total_sessions_90d=counts['90d'],
                tutor_reschedules_7d=reschedule_counts['7d'],
                tutor_reschedules_30d=reschedule_counts['30d'],
                tutor_reschedules_90d=reschedule_counts['90d'],
                is_high_risk=is_high_risk,
                risk_threshold=RISK_THRESHOLD,
                last_calculated_at=now
            )
            db.add(tutor_score)
        
        tutor_scores.append(tutor_score)
    
    db.commit()
    print(f"✓ Calculated scores for {len(tutor_scores)} tutors")
    
    return tutor_scores


def clear_existing_data(db: SessionLocal) -> None:
    """Clear all existing data from database."""
    print("Clearing existing data...")
    
    # Delete in order respecting foreign keys
    db.query(EmailReport).delete()
    db.query(Reschedule).delete()
    db.query(TutorScore).delete()
    db.query(Session).delete()
    db.query(Tutor).delete()
    
    db.commit()
    print("✓ Cleared all existing data")


def validate_data(db: SessionLocal) -> Dict:
    """Validate generated data quality."""
    print("\nValidating data quality...")
    
    tutor_count = db.query(Tutor).count()
    session_count = db.query(Session).count()
    reschedule_count = db.query(Reschedule).count()
    tutor_score_count = db.query(TutorScore).count()
    
    # Check foreign keys
    orphaned_sessions = db.query(Session).filter(
        ~Session.tutor_id.in_(db.query(Tutor.id))
    ).count()
    
    orphaned_reschedules = db.query(Reschedule).filter(
        ~Reschedule.session_id.in_(db.query(Session.id))
    ).count()
    
    # Check reschedule rates
    high_risk_count = db.query(TutorScore).filter_by(is_high_risk=True).count()
    
    validation_report = {
        'tutor_count': tutor_count,
        'session_count': session_count,
        'reschedule_count': reschedule_count,
        'tutor_score_count': tutor_score_count,
        'high_risk_tutors': high_risk_count,
        'orphaned_sessions': orphaned_sessions,
        'orphaned_reschedules': orphaned_reschedules,
        'valid': orphaned_sessions == 0 and orphaned_reschedules == 0
    }
    
    print(f"✓ Validation complete")
    return validation_report


def print_summary(validation_report: Dict) -> None:
    """Print summary statistics."""
    print("\n" + "="*60)
    print("DATA GENERATION SUMMARY")
    print("="*60)
    print(f"Tutors created:           {validation_report['tutor_count']}")
    print(f"Sessions created:        {validation_report['session_count']}")
    print(f"Reschedules created:     {validation_report['reschedule_count']}")
    print(f"Tutor scores calculated: {validation_report['tutor_score_count']}")
    print(f"High-risk tutors:       {validation_report['high_risk_tutors']}")
    print(f"Orphaned sessions:       {validation_report['orphaned_sessions']}")
    print(f"Orphaned reschedules:    {validation_report['orphaned_reschedules']}")
    print(f"Data valid:              {'✓' if validation_report['valid'] else '✗'}")
    print("="*60)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate synthetic data for Tutor Quality Scoring System')
    parser.add_argument('--tutors', type=int, default=100, help='Number of tutors to generate')
    parser.add_argument('--sessions', type=int, default=3000, help='Number of sessions to generate')
    parser.add_argument('--days', type=int, default=90, help='Number of days to generate sessions over')
    parser.add_argument('--clear-existing', action='store_true', help='Clear existing data before generating')
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        if args.clear_existing:
            clear_existing_data(db)
        
        # Generate data
        start_date = datetime.utcnow() - timedelta(days=180)
        tutors = generate_tutors(db, args.tutors, start_date)
        sessions = generate_sessions(db, tutors, args.sessions, args.days)
        reschedules = generate_reschedules(db, sessions)
        tutor_scores = calculate_tutor_scores(db, tutors)
        
        # Validate
        validation_report = validate_data(db)
        print_summary(validation_report)
        
        if not validation_report['valid']:
            print("\n⚠ WARNING: Data validation failed!")
            sys.exit(1)
        
        print("\n✓ Data generation completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()

