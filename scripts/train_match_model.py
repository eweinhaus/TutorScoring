#!/usr/bin/env python3
"""
Train XGBoost model for match prediction.

This script:
1. Generates synthetic training data
2. Trains an XGBoost binary classifier
3. Evaluates model performance
4. Saves model and metadata

Run with: python scripts/train_match_model.py
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

try:
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.utils.class_weight import compute_sample_weight
    import xgboost as xgb
    import joblib
    from faker import Faker
except ImportError as e:
    print(f"Error: Missing required dependencies. Please install: pip install xgboost scikit-learn pandas numpy joblib faker")
    print(f"Missing: {e}")
    sys.exit(1)

from app.services.feature_engineering import extract_features, calculate_mismatch_scores, calculate_compatibility_score
from app.models.student import Student
from app.models.tutor import Tutor


def generate_synthetic_training_data(num_samples: int = 1000, target_churn_rate: float = 0.12) -> tuple:
    """
    Generate synthetic training data for model training.
    
    Uses realistic churn distribution: ~10-12% of matches have high churn risk.
    This reflects industry standards where most matches are good, with only
    a small percentage having significant compatibility issues.
    
    NOTE: Currently uses synthetic data. To train on real historical churn data:
    1. Track actual churn outcomes (student-tutor pairs that resulted in churn)
    2. Query MatchPrediction table with actual outcomes
    3. Use real features and actual churn labels from database
    
    Args:
        num_samples: Number of student-tutor pairs to generate
        target_churn_rate: Target churn rate (default 0.12 = 12%)
        
    Returns:
        Tuple of (X: feature matrix, y: labels, feature_names)
    """
    fake = Faker()
    X_data = []
    y_data = []
    
    print(f"Generating {num_samples} synthetic training samples...")
    print(f"Target churn rate: {target_churn_rate:.1%}")
    
    # Track statistics
    churn_count = 0
    compatibility_scores = []
    
    for i in range(num_samples):
        # Create synthetic student
        student = Student(
            id=None,  # Not saved to DB
            name=fake.name(),
            age=fake.random_int(min=12, max=18),
            sex=fake.random_element(elements=('male', 'female', None)),
            preferred_pace=fake.random_int(min=1, max=5),
            preferred_teaching_style=fake.random_element(elements=('structured', 'flexible', 'interactive')),
            communication_style_preference=fake.random_int(min=1, max=5),
            urgency_level=fake.random_int(min=1, max=5),
            previous_tutoring_experience=fake.random_int(min=0, max=50),
            previous_satisfaction=fake.random_int(min=1, max=5),
        )
        
        # Create synthetic tutor
        tutor = Tutor(
            id=None,  # Not saved to DB
            name=fake.name(),
            age=fake.random_int(min=22, max=45),
            sex=fake.random_element(elements=('male', 'female', None)),
            experience_years=fake.random_int(min=0, max=10),
            teaching_style=fake.random_element(elements=('structured', 'flexible', 'interactive')),
            preferred_pace=fake.random_int(min=1, max=5),
            communication_style=fake.random_int(min=1, max=5),
            confidence_level=fake.random_int(min=1, max=5),
        )
        
        # Extract features
        features = extract_features(student, tutor)
        
        # Calculate compatibility score
        mismatch_scores = calculate_mismatch_scores(student, tutor)
        compatibility = calculate_compatibility_score(mismatch_scores)
        compatibility_scores.append(compatibility)
        
        # Generate realistic churn label
        # Strategy: Use a threshold that results in ~12% churn rate
        # Most real-world matches have decent compatibility (right-skewed distribution)
        # Only matches with very poor compatibility (< ~0.4) should churn
        
        # Churn probability: inverse of compatibility
        churn_prob = 1.0 - compatibility
        
        # Add realistic noise (smaller variance for more realistic distribution)
        churn_prob += np.random.normal(0, 0.08)
        churn_prob = max(0, min(1, churn_prob))
        
        # Use adaptive threshold based on target churn rate
        # For ~12% churn, we need threshold around 0.76-0.88
        # This means only very poor matches (compatibility < 0.12-0.24) churn
        # Threshold: inverse of target churn rate, adjusted for noise
        # Higher threshold = fewer churn labels
        threshold = 1.0 - target_churn_rate - 0.03  # ~0.85 for 12% target (accounts for noise)
        
        # Binary label: 1 if churn_prob > threshold, else 0
        # This ensures only the worst matches (highest churn prob) get labeled as churn
        label = 1 if churn_prob > threshold else 0
        
        if label == 1:
            churn_count += 1
        
        # Store features in consistent order
        feature_names = sorted(features.keys())
        X_data.append([features[name] for name in feature_names])
        y_data.append(label)
        
        if (i + 1) % 100 == 0:
            current_rate = churn_count / (i + 1)
            print(f"  Generated {i + 1}/{num_samples} samples... (churn rate: {current_rate:.1%})")
    
    X = np.array(X_data)
    y = np.array(y_data)
    
    # Final statistics
    actual_churn_rate = np.mean(y)
    avg_compatibility = np.mean(compatibility_scores)
    
    print(f"\nTraining data statistics:")
    print(f"  Total samples: {num_samples}")
    print(f"  Churn labels: {churn_count} ({actual_churn_rate:.1%})")
    print(f"  No-churn labels: {num_samples - churn_count} ({1-actual_churn_rate:.1%})")
    print(f"  Average compatibility: {avg_compatibility:.3f}")
    print(f"  Target churn rate: {target_churn_rate:.1%}")
    print(f"  Actual churn rate: {actual_churn_rate:.1%}")
    
    if abs(actual_churn_rate - target_churn_rate) > 0.05:
        print(f"  ⚠️  Warning: Actual churn rate ({actual_churn_rate:.1%}) differs from target ({target_churn_rate:.1%})")
        print(f"     This is expected due to random sampling. Model will learn the actual distribution.")
    
    return X, y, feature_names


def train_model(X: np.ndarray, y: np.ndarray, feature_names: list) -> tuple:
    """
    Train XGBoost model and evaluate performance.
    
    Args:
        X: Feature matrix
        y: Labels
        feature_names: List of feature names
        
    Returns:
        Tuple of (model, feature_names, metrics)
    """
    print("\nTraining model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"  Training set: {len(X_train)} samples")
    print(f"  Test set: {len(X_test)} samples")
    
    # Initialize model with class weighting to handle imbalanced data
    # Since we have ~12% churn (class 1) vs ~88% no-churn (class 0),
    # we want to weight the positive class appropriately
    
    # Calculate class weights: more weight to minority class (churn)
    sample_weights = compute_sample_weight('balanced', y_train)
    
    # Initialize base model (uncalibrated)
    base_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss',
        scale_pos_weight=len(y_train[y_train == 0]) / len(y_train[y_train == 1])  # Handle class imbalance
    )
    
    # Train base model with sample weights to handle class imbalance
    base_model.fit(X_train, y_train, sample_weight=sample_weights)
    
    # Calibrate the model using Platt scaling (logistic regression)
    # This will make probabilities more realistic and less overconfident
    print("\nCalibrating model probabilities...")
    print("  Using Platt scaling (isotonic regression) to reduce overconfidence")
    model = CalibratedClassifierCV(
        base_model,
        method='isotonic',  # Use isotonic regression for better calibration
        cv=3,  # 3-fold cross-validation for calibration
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Check calibration before/after
    print("\nChecking probability calibration...")
    # Get uncalibrated predictions for comparison
    y_pred_proba_uncalibrated = base_model.predict_proba(X_test)[:, 1]
    
    # Calculate calibration metrics
    def count_extreme_probs(probs, threshold_low=0.01, threshold_high=0.9):
        """Count extremely confident predictions."""
        very_low = sum(1 for p in probs if p < threshold_low)
        very_high = sum(1 for p in probs if p >= threshold_high)
        return very_low, very_high
    
    uncal_low, uncal_high = count_extreme_probs(y_pred_proba_uncalibrated)
    cal_low, cal_high = count_extreme_probs(y_pred_proba)
    
    print(f"  Uncalibrated - Very low (<1%): {uncal_low}/{len(y_test)} ({uncal_low/len(y_test)*100:.1f}%)")
    print(f"  Uncalibrated - Very high (>=90%): {uncal_high}/{len(y_test)} ({uncal_high/len(y_test)*100:.1f}%)")
    print(f"  Calibrated - Very low (<1%): {cal_low}/{len(y_test)} ({cal_low/len(y_test)*100:.1f}%)")
    print(f"  Calibrated - Very high (>=90%): {cal_high}/{len(y_test)} ({cal_high/len(y_test)*100:.1f}%)")
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    metrics = {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'roc_auc': float(roc_auc),
    }
    
    print("\nModel Performance:")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1 Score:  {metrics['f1_score']:.4f}")
    print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
    
    # Feature importance (get from base model)
    base_model_for_importance = model.calibrated_classifiers_[0].estimator if hasattr(model, 'calibrated_classifiers_') else base_model
    feature_importance = dict(zip(feature_names, base_model_for_importance.feature_importances_.tolist()))
    print("\nTop 10 Most Important Features:")
    for name, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {name}: {importance:.4f}")
    
    return model, feature_names, metrics


def save_model(model, feature_names: list, metrics: dict, model_dir: Path):
    """
    Save trained and calibrated model and metadata to disk.
    
    Args:
        model: Trained and calibrated XGBoost model (CalibratedClassifierCV)
        feature_names: List of feature names
        metrics: Model performance metrics
        model_dir: Directory to save model files
    """
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model (CalibratedClassifierCV wraps the base model)
    model_path = model_dir / 'match_model.pkl'
    joblib.dump(model, model_path)
    print(f"\nCalibrated model saved to: {model_path}")
    
    # Save feature names
    feature_names_path = model_dir / 'feature_names.json'
    with open(feature_names_path, 'w') as f:
        json.dump(feature_names, f, indent=2)
    print(f"Feature names saved to: {feature_names_path}")
    
    # Save metadata
    metadata = {
        'model_version': 'v1.1',  # Updated version for calibrated model
        'trained_at': datetime.utcnow().isoformat(),
        'metrics': metrics,
        'feature_count': len(feature_names),
        'calibrated': True,  # Mark that this model is calibrated
        'calibration_method': 'isotonic',
    }
    metadata_path = model_dir / 'model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")


def main():
    """Main training function."""
    print("=" * 60)
    print("Match Prediction Model Training")
    print("=" * 60)
    
    # Get model directory
    backend_dir = Path(__file__).parent.parent / 'backend'
    model_dir = backend_dir / 'models'
    
    # Generate training data with realistic ~12% churn rate
    # This reflects industry standards where most matches are good,
    # with only ~10-12% having high churn risk
    # Note: "24% of churners fail at first session" means 24% of those who churn,
    # not 24% overall churn rate. Overall churn should be ~10-12%.
    X, y, feature_names = generate_synthetic_training_data(
        num_samples=1000,
        target_churn_rate=0.12  # 12% realistic churn rate
    )
    
    # Train model
    model, feature_names, metrics = train_model(X, y, feature_names)
    
    # Save model
    save_model(model, feature_names, metrics, model_dir)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)
    
    # Check if precision meets threshold
    if metrics['precision'] < 0.70:
        print(f"\n⚠️  Warning: Precision ({metrics['precision']:.4f}) is below 0.70 threshold.")
        print("   Consider increasing training data or tuning hyperparameters.")
    else:
        print(f"\n✅ Model precision ({metrics['precision']:.4f}) meets 0.70 threshold.")


if __name__ == '__main__':
    main()

