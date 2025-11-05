#!/usr/bin/env python3
"""
Generate synthetic data for matching service.

This script:
1. Generates student profiles
2. Enhances existing tutors with preferences
3. Generates match predictions for all student-tutor pairs

Usage:
    python scripts/generate_matching_data.py --num-students 20
    python scripts/generate_matching_data.py --num-students 50 --reset
    python scripts/generate_matching_data.py --generate-predictions
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from sqlalchemy.orm import Session
from faker import Faker
try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm not installed
    def tqdm(iterable, desc=None):
        return iterable

from app.utils.database import get_db
from app.models.student import Student
from app.models.tutor import Tutor
from app.models.match_prediction import MatchPrediction
from app.services.match_prediction_service import get_or_create_match_prediction
from app.services.tutor_service import get_tutor_stats

fake = Faker()


def clear_existing_data(db: Session, reset_students: bool = False, reset_predictions: bool = True):
    """Clear existing matching data."""
    if reset_predictions:
        print("Clearing existing match predictions...")
        deleted = db.query(MatchPrediction).delete()
        db.commit()
        print(f"  Deleted {deleted} match predictions")
    
    if reset_students:
        print("Clearing existing students...")
        deleted = db.query(Student).delete()
        db.commit()
        print(f"  Deleted {deleted} students")


def generate_students(db: Session, num_students: int):
    """Generate student profiles."""
    print(f"\nGenerating {num_students} students...")
    
    students = []
    teaching_styles = ['structured', 'flexible', 'interactive', 'traditional', 'modern']
    
    for i in tqdm(range(num_students), desc="Creating students"):
        student = Student(
            name=fake.name(),
            age=fake.random_int(min=12, max=18),
            sex=fake.random_element(elements=('male', 'female', None)),
            preferred_pace=fake.random_int(min=1, max=5),
            preferred_teaching_style=fake.random_element(elements=teaching_styles),
            communication_style_preference=fake.random_int(min=1, max=5),
            urgency_level=fake.random_int(min=1, max=5),
            learning_goals=fake.text(max_nb_chars=200) if fake.boolean(chance_of_getting_true=70) else None,
            previous_tutoring_experience=fake.random_int(min=0, max=50),
            previous_satisfaction=fake.random_int(min=1, max=5) if fake.boolean(chance_of_getting_true=60) else None,
        )
        students.append(student)
    
    # Bulk insert
    db.bulk_save_objects(students)
    db.commit()
    
    # Refresh to get IDs
    for student in students:
        db.refresh(student)
    
    print(f"  ✅ Created {len(students)} students")
    return students


def enhance_tutors(db: Session):
    """Enhance existing tutors with matching preferences."""
    print("\nEnhancing tutors with preferences...")
    
    tutors = db.query(Tutor).all()
    teaching_styles = ['structured', 'flexible', 'interactive', 'traditional', 'modern']
    
    enhanced_count = 0
    for tutor in tqdm(tutors, desc="Enhancing tutors"):
        # Only enhance if preferences not already set
        if tutor.age is None and tutor.preferred_pace is None:
            tutor.age = fake.random_int(min=22, max=45)
            tutor.sex = fake.random_element(elements=('male', 'female', None))
            tutor.experience_years = fake.random_int(min=0, max=10)
            tutor.teaching_style = fake.random_element(elements=teaching_styles)
            tutor.preferred_pace = fake.random_int(min=1, max=5)
            tutor.communication_style = fake.random_int(min=1, max=5)
            tutor.confidence_level = fake.random_int(min=1, max=5)
            tutor.preferred_student_level = fake.random_element(
                elements=('beginner', 'intermediate', 'advanced', None)
            )
            enhanced_count += 1
    
    db.commit()
    print(f"  ✅ Enhanced {enhanced_count} tutors")
    return tutors


def generate_predictions(db: Session, batch_size: int = 100):
    """Generate match predictions for all student-tutor pairs."""
    print("\nGenerating match predictions...")
    
    students = db.query(Student).all()
    tutors = db.query(Tutor).all()
    
    if not students:
        print("  ⚠️  No students found. Run with --num-students to create students first.")
        return
    
    if not tutors:
        print("  ⚠️  No tutors found. Please ensure tutors exist in database.")
        return
    
    total_pairs = len(students) * len(tutors)
    print(f"  Generating predictions for {total_pairs} student-tutor pairs...")
    
    predictions_created = 0
    predictions_existing = 0
    
    # Process in batches
    for student in tqdm(students, desc="Processing students"):
        for tutor in tutors:
            # Get tutor stats for better prediction
            tutor_stats = None
            if tutor.tutor_score:
                tutor_stats = {
                    'reschedule_rate_30d': float(tutor.tutor_score.reschedule_rate_30d or 0),
                    'total_sessions_30d': tutor.tutor_score.total_sessions_30d,
                    'is_high_risk': tutor.tutor_score.is_high_risk,
                }
            
            # Check if prediction already exists
            existing = db.query(MatchPrediction).filter(
                MatchPrediction.student_id == student.id,
                MatchPrediction.tutor_id == tutor.id
            ).first()
            
            if existing:
                predictions_existing += 1
                continue
            
            # Create prediction
            try:
                match_prediction = get_or_create_match_prediction(
                    db, student, tutor, tutor_stats
                )
                predictions_created += 1
            except Exception as e:
                print(f"  ⚠️  Error creating prediction for {student.name} - {tutor.name}: {e}")
                continue
    
    print(f"\n  ✅ Created {predictions_created} new predictions")
    print(f"  ✅ Skipped {predictions_existing} existing predictions")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate matching service data')
    parser.add_argument('--num-students', type=int, default=20, help='Number of students to generate')
    parser.add_argument('--reset', action='store_true', help='Reset existing data (students and predictions)')
    parser.add_argument('--reset-students', action='store_true', help='Reset students only')
    parser.add_argument('--reset-predictions', action='store_true', help='Reset predictions only')
    parser.add_argument('--generate-predictions', action='store_true', help='Generate predictions for all pairs')
    parser.add_argument('--enhance-tutors', action='store_true', help='Enhance tutors with preferences')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Matching Service Data Generation")
    print("=" * 60)
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Clear existing data if requested
        if args.reset:
            clear_existing_data(db, reset_students=True, reset_predictions=True)
        elif args.reset_students:
            clear_existing_data(db, reset_students=True, reset_predictions=False)
        elif args.reset_predictions:
            clear_existing_data(db, reset_students=False, reset_predictions=True)
        
        # Generate students
        if args.num_students > 0:
            generate_students(db, args.num_students)
        
        # Enhance tutors
        if args.enhance_tutors or args.num_students > 0:
            enhance_tutors(db)
        
        # Generate predictions
        if args.generate_predictions or args.num_students > 0:
            generate_predictions(db)
        
        print("\n" + "=" * 60)
        print("Data generation complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    main()

