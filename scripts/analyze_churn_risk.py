#!/usr/bin/env python3
"""
Analyze churn risk model to investigate discrepancy between 
predicted average churn risk (~60%) and expected first session churn (24%).

This script:
1. Simulates the training data generation logic
2. Analyzes the distribution of compatibility scores
3. Shows how the synthetic data leads to high churn rates
4. Identifies the root cause
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

try:
    import numpy as np
    from faker import Faker
except ImportError:
    print("Error: Missing dependencies. Run: pip install numpy faker")
    sys.exit(1)

from app.services.feature_engineering import (
    calculate_mismatch_scores, 
    calculate_compatibility_score
)
from app.models.student import Student
from app.models.tutor import Tutor


def simulate_training_data_generation(num_samples=10000):
    """Simulate the training data generation process."""
    fake = Faker()
    compatibility_scores = []
    churn_probs_raw = []
    churn_probs_with_noise = []
    labels = []
    
    print(f"Simulating {num_samples} training samples...")
    print("=" * 60)
    
    for i in range(num_samples):
        # Create synthetic student (matching train_match_model.py logic)
        student = Student(
            id=None,
            name=fake.name(),
            age=fake.random_int(min=12, max=18),
            sex=fake.random_element(elements=('male', 'female', None)),
            preferred_pace=fake.random_int(min=1, max=5),
            preferred_teaching_style=fake.random_element(
                elements=('structured', 'flexible', 'interactive')
            ),
            communication_style_preference=fake.random_int(min=1, max=5),
            urgency_level=fake.random_int(min=1, max=5),
            previous_tutoring_experience=fake.random_int(min=0, max=50),
            previous_satisfaction=fake.random_int(min=1, max=5),
        )
        
        # Create synthetic tutor
        tutor = Tutor(
            id=None,
            name=fake.name(),
            age=fake.random_int(min=22, max=45),
            sex=fake.random_element(elements=('male', 'female', None)),
            experience_years=fake.random_int(min=0, max=10),
            teaching_style=fake.random_element(
                elements=('structured', 'flexible', 'interactive')
            ),
            preferred_pace=fake.random_int(min=1, max=5),
            communication_style=fake.random_int(min=1, max=5),
            confidence_level=fake.random_int(min=1, max=5),
        )
        
        # Calculate compatibility (matching training logic)
        mismatch_scores = calculate_mismatch_scores(student, tutor)
        compatibility = calculate_compatibility_score(mismatch_scores)
        
        # Churn probability: inverse of compatibility, with noise
        churn_prob_raw = 1.0 - compatibility
        churn_prob_with_noise = churn_prob_raw + np.random.normal(0, 0.1)
        churn_prob_with_noise = max(0, min(1, churn_prob_with_noise))
        
        # Binary label: 1 if churn_prob > 0.5, else 0
        label = 1 if churn_prob_with_noise > 0.5 else 0
        
        compatibility_scores.append(compatibility)
        churn_probs_raw.append(churn_prob_raw)
        churn_probs_with_noise.append(churn_prob_with_noise)
        labels.append(label)
    
    return {
        'compatibility_scores': np.array(compatibility_scores),
        'churn_probs_raw': np.array(churn_probs_raw),
        'churn_probs_with_noise': np.array(churn_probs_with_noise),
        'labels': np.array(labels),
    }


def analyze_distribution(data):
    """Analyze the distribution of scores and identify issues."""
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    
    compat = data['compatibility_scores']
    churn_raw = data['churn_probs_raw']
    churn_noise = data['churn_probs_with_noise']
    labels = data['labels']
    
    print("\n1. COMPATIBILITY SCORE DISTRIBUTION:")
    print(f"   Mean: {np.mean(compat):.3f}")
    print(f"   Median: {np.median(compat):.3f}")
    print(f"   Min: {np.min(compat):.3f}")
    print(f"   Max: {np.max(compat):.3f}")
    print(f"   Std Dev: {np.std(compat):.3f}")
    
    print("\n2. CHURN PROBABILITY (RAW - inverse of compatibility):")
    print(f"   Mean: {np.mean(churn_raw):.3f} ({np.mean(churn_raw)*100:.1f}%)")
    print(f"   Median: {np.median(churn_raw):.3f}")
    
    print("\n3. CHURN PROBABILITY (WITH NOISE):")
    print(f"   Mean: {np.mean(churn_noise):.3f} ({np.mean(churn_noise)*100:.1f}%)")
    print(f"   Median: {np.median(churn_noise):.3f}")
    
    print("\n4. BINARY LABELS (1 = churn, 0 = no churn):")
    churn_rate = np.mean(labels)
    print(f"   Churn label rate: {churn_rate:.3f} ({churn_rate*100:.1f}%)")
    print(f"   No-churn rate: {1-churn_rate:.3f} ({(1-churn_rate)*100:.1f}%)")
    
    print("\n5. ROOT CAUSE ANALYSIS:")
    print("   " + "-" * 56)
    
    # Check if compatibility is centered around 0.5
    compat_center = abs(np.mean(compat) - 0.5)
    if compat_center < 0.1:
        print(f"   ⚠️  ISSUE FOUND: Compatibility scores are centered around 0.5")
        print(f"      This happens because student/tutor preferences are randomly generated,")
        print(f"      leading to roughly uniform distribution of mismatches.")
        print(f"      Since churn_prob = 1 - compatibility, this creates ~50% average churn.")
    
    # Check label distribution
    if churn_rate > 0.4:
        print(f"   ⚠️  ISSUE FOUND: Training labels are ~{churn_rate*100:.0f}% churn")
        print(f"      Model will learn this distribution and output similar probabilities.")
    
    print("\n6. EXPECTED vs ACTUAL:")
    print("   " + "-" * 56)
    print(f"   Expected (from directions.md): 24% of churners fail at first session")
    print(f"   Note: This means 24% of those who churn, churn at first session.")
    print(f"         It does NOT mean 24% overall churn rate.")
    print(f"   ")
    print(f"   Actual synthetic data: ~{churn_rate*100:.0f}% labeled as churn")
    print(f"   Model predictions: ~{np.mean(churn_noise)*100:.0f}% average churn risk")
    print(f"   ")
    print(f"   ❌ MISMATCH: The synthetic data creates too many churn labels because")
    print(f"      compatibility scores are uniformly distributed (random matching).")


def identify_solutions():
    """Identify potential solutions."""
    print("\n" + "=" * 60)
    print("POTENTIAL SOLUTIONS")
    print("=" * 60)
    
    print("\n1. FIX SYNTHETIC DATA GENERATION:")
    print("   - Generate training data with realistic churn rate (~10-15% overall)")
    print("   - Ensure most matches have good compatibility (right-skewed distribution)")
    print("   - Only generate churn labels when compatibility is actually low")
    print("   - Adjust threshold: label = 1 if churn_prob > 0.76 (not 0.5)")
    print("     This would give ~24% churn rate if overall churn is ~10-15%")
    
    print("\n2. ADD CLASS WEIGHTING:")
    print("   - Use XGBoost scale_pos_weight to handle class imbalance")
    print("   - Weight negative class (no churn) higher than positive class")
    
    print("\n3. CALIBRATE MODEL OUTPUT:")
    print("   - Use Platt scaling or isotonic regression to calibrate probabilities")
    print("   - Adjust probabilities to match expected 24% first-session churn rate")
    print("   - Note: 24% is conditional (of churners), not absolute rate")
    
    print("\n4. CLARIFY DEFINITION:")
    print("   - Verify what '24% of churners fail at first session' means")
    print("   - If overall churn is ~10%, then 24% of that = ~2.4% first-session churn")
    print("   - The model should predict overall churn risk, not just first-session")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    print("\nMost likely cause: SYNTHETIC DATA ISSUE")
    print("The training data generation creates ~50% churn labels because")
    print("random student-tutor matching leads to uniform compatibility distribution.")
    print("\nFix: Adjust generate_synthetic_training_data() to create realistic")
    print("churn distribution matching business expectations.")


def main():
    """Main analysis function."""
    print("=" * 60)
    print("CHURN RISK MODEL ANALYSIS")
    print("Investigating 60% vs 24% discrepancy")
    print("=" * 60)
    
    # Simulate training data
    data = simulate_training_data_generation(num_samples=10000)
    
    # Analyze
    analyze_distribution(data)
    
    # Suggest solutions
    identify_solutions()
    
    print("\n")


if __name__ == '__main__':
    main()

