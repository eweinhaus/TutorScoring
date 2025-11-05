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


def generate_synthetic_training_data(num_samples: int = 1000) -> tuple:
    """
    Generate synthetic training data for model training.
    
    Args:
        num_samples: Number of student-tutor pairs to generate
        
    Returns:
        Tuple of (X: feature matrix, y: labels)
    """
    fake = Faker()
    X_data = []
    y_data = []
    
    print(f"Generating {num_samples} synthetic training samples...")
    
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
        
        # Generate label based on mismatch patterns
        # High mismatch = likely churn (label=1), low mismatch = no churn (label=0)
        mismatch_scores = calculate_mismatch_scores(student, tutor)
        compatibility = calculate_compatibility_score(mismatch_scores)
        
        # Churn probability: inverse of compatibility, with some randomness
        churn_prob = 1.0 - compatibility
        # Add some realistic noise
        churn_prob += np.random.normal(0, 0.1)
        churn_prob = max(0, min(1, churn_prob))
        
        # Binary label: 1 if churn_prob > 0.5, else 0
        label = 1 if churn_prob > 0.5 else 0
        
        # Store features in consistent order
        feature_names = sorted(features.keys())
        X_data.append([features[name] for name in feature_names])
        y_data.append(label)
        
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{num_samples} samples...")
    
    X = np.array(X_data)
    y = np.array(y_data)
    
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
    
    # Initialize model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss'
    )
    
    # Train model
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
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
    
    # Feature importance
    feature_importance = dict(zip(feature_names, model.feature_importances_.tolist()))
    print("\nTop 10 Most Important Features:")
    for name, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {name}: {importance:.4f}")
    
    return model, feature_names, metrics


def save_model(model, feature_names: list, metrics: dict, model_dir: Path):
    """
    Save model and metadata to disk.
    
    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        metrics: Performance metrics
        model_dir: Directory to save model files
    """
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = model_dir / 'match_model.pkl'
    joblib.dump(model, model_path)
    print(f"\nModel saved to: {model_path}")
    
    # Save feature names
    feature_names_path = model_dir / 'feature_names.json'
    with open(feature_names_path, 'w') as f:
        json.dump(feature_names, f, indent=2)
    print(f"Feature names saved to: {feature_names_path}")
    
    # Save metadata
    metadata = {
        'model_version': 'v1.0',
        'trained_at': datetime.utcnow().isoformat(),
        'metrics': metrics,
        'feature_count': len(feature_names),
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
    
    # Generate training data
    X, y, feature_names = generate_synthetic_training_data(num_samples=1000)
    
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

