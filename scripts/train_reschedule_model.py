#!/usr/bin/env python3
"""
Train XGBoost model for reschedule prediction.

This script:
1. Extracts historical training data from database OR generates synthetic data
2. Trains an XGBoost binary classifier
3. Evaluates model performance
4. Saves model and metadata

Run with: python scripts/train_reschedule_model.py
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

try:
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.utils.class_weight import compute_sample_weight
    import xgboost as xgb
    import joblib
    from faker import Faker
except ImportError as e:
    print(f"Error: Missing required dependencies. Please install: pip install xgboost scikit-learn pandas numpy joblib faker")
    print(f"Missing: {e}")
    sys.exit(1)

from app.services.reschedule_feature_engineering import extract_features
from app.models.session import Session
from app.models.tutor import Tutor
from app.models.reschedule import Reschedule
from app.services.tutor_service import get_tutor_statistics
from app.utils.database import SessionLocal


def extract_historical_training_data(db, min_sessions: int = 500):
    """
    Extract historical training data from database.
    
    Args:
        db: Database session
        min_sessions: Minimum number of sessions required
        
    Returns:
        Tuple of (X: feature matrix, y: labels, feature_names)
    """
    print(f"Extracting historical training data (minimum: {min_sessions} sessions)...")
    
    # Query sessions from last 90 days
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    
    sessions = db.query(Session).filter(
        Session.status.in_(['completed', 'rescheduled']),
        Session.scheduled_time >= cutoff_date
    ).order_by(Session.scheduled_time).all()
    
    print(f"Found {len(sessions)} sessions in last 90 days")
    
    if len(sessions) < min_sessions:
        print(f"⚠️  Insufficient historical data: {len(sessions)} < {min_sessions}")
        return None, None, None
    
    X_data = []
    y_data = []
    feature_names_set = set()
    
    reschedule_count = 0
    
    for i, session in enumerate(sessions):
        try:
            # Get tutor
            tutor = session.tutor
            if not tutor:
                continue
            
            # Get tutor stats
            tutor_stats = get_tutor_statistics(str(tutor.id), db)
            
            # Extract features
            features = extract_features(session, tutor_stats, db)
            
            # Store feature names (first time)
            if not feature_names_set:
                feature_names_set = set(features.keys())
            
            # Determine label: 1.0 if rescheduled by tutor, else 0.0
            label = 0.0
            if session.status == 'rescheduled' and session.reschedule:
                if session.reschedule.initiator == 'tutor':
                    label = 1.0
                    reschedule_count += 1
            
            # Store features in consistent order
            sorted_features = sorted(features.items())
            if i == 0:
                feature_names = [k for k, v in sorted_features]
            X_data.append([v for k, v in sorted_features])
            y_data.append(label)
            
            if (i + 1) % 100 == 0:
                current_rate = reschedule_count / (i + 1)
                print(f"  Processed {i + 1}/{len(sessions)} sessions... (reschedule rate: {current_rate:.1%})")
        
        except Exception as e:
            print(f"  ⚠️  Error processing session {session.id}: {e}")
            continue
    
    if len(X_data) == 0:
        print("❌ No valid training samples extracted")
        return None, None, None
    
    X = np.array(X_data)
    y = np.array(y_data)
    feature_names = sorted(feature_names_set)
    
    actual_reschedule_rate = np.mean(y)
    
    print(f"\nHistorical data statistics:")
    print(f"  Total samples: {len(X_data)}")
    print(f"  Reschedule labels: {reschedule_count} ({actual_reschedule_rate:.1%})")
    print(f"  No-reschedule labels: {len(X_data) - reschedule_count} ({1-actual_reschedule_rate:.1%})")
    print(f"  Feature count: {len(feature_names)}")
    
    if actual_reschedule_rate < 0.05 or actual_reschedule_rate > 0.30:
        print(f"  ⚠️  Warning: Reschedule rate ({actual_reschedule_rate:.1%}) is outside typical range (5-30%)")
    
    return X, y, feature_names


def generate_synthetic_training_data(num_samples: int = 1000, target_reschedule_rate: float = 0.10):
    """
    Generate synthetic training data for model training.
    
    Args:
        num_samples: Number of sessions to generate
        target_reschedule_rate: Target reschedule rate (default 0.10 = 10%)
        
    Returns:
        Tuple of (X: feature matrix, y: labels, feature_names)
    """
    print(f"Generating {num_samples} synthetic training samples...")
    print(f"Target reschedule rate: {target_reschedule_rate:.1%}")
    
    fake = Faker()
    X_data = []
    y_data = []
    feature_names_set = set()
    feature_names = None  # Will be set in first iteration
    reschedule_count = 0
    
    # Create a mock database session for feature extraction
    # We'll need to create Session objects without actually saving them
    from app.models.base import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create in-memory database for feature extraction
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SyntheticSession = sessionmaker(bind=engine)
    db = SyntheticSession()
    
    for i in range(num_samples):
        try:
            # Create synthetic tutor
            tutor = Tutor(
                id=None,  # Not saved
                name=fake.name(),
                email=fake.email(),
                age=fake.random_int(min=22, max=45),
                experience_years=fake.random_int(min=0, max=10),
                confidence_level=fake.random_int(min=1, max=5),
                communication_style=fake.random_int(min=1, max=5),
                is_active=True
            )
            
            # Create synthetic session
            scheduled_time = fake.date_time_between(start_date='-30d', end_date='+7d')
            session = Session(
                id=None,  # Not saved
                tutor_id=fake.uuid4(),
                student_id=fake.uuid4().hex[:8],
                scheduled_time=scheduled_time,
                status='scheduled',  # Will be determined below
                duration_minutes=fake.random_int(min=30, max=120),
                tutor=tutor
            )
            
            # Determine tutor reschedule rate (simulate different tutor patterns)
            # High-risk tutors: 20-40% reschedule rate
            # Medium-risk tutors: 10-20% reschedule rate
            # Low-risk tutors: 0-10% reschedule rate
            tutor_risk_level = fake.random_element(elements=['low', 'medium', 'high'])
            if tutor_risk_level == 'high':
                tutor_reschedule_rate = fake.random.uniform(0.20, 0.40)
            elif tutor_risk_level == 'medium':
                tutor_reschedule_rate = fake.random.uniform(0.10, 0.20)
            else:
                tutor_reschedule_rate = fake.random.uniform(0.0, 0.10)
            
            # Create tutor_stats dict
            tutor_stats = {
                'reschedule_rate_7d': tutor_reschedule_rate * 100,
                'reschedule_rate_30d': tutor_reschedule_rate * 100,
                'reschedule_rate_90d': tutor_reschedule_rate * 100,
                'total_sessions_7d': fake.random_int(min=5, max=20),
                'total_sessions_30d': fake.random_int(min=10, max=50),
                'total_sessions_90d': fake.random_int(min=20, max=100),
                'is_high_risk': tutor_reschedule_rate > 0.15,
            }
            
            # Extract features (this will work with our synthetic data)
            # Note: session_context features will be minimal since we're not saving to DB
            features = extract_features(session, tutor_stats, db)
            
            # Store feature names (first time)
            if not feature_names_set:
                feature_names_set = set(features.keys())
            
            # Generate label based on realistic patterns
            # Base probability: tutor reschedule rate
            base_prob = tutor_reschedule_rate
            
            # Adjustments:
            # - Weekend sessions: +5%
            # - First-time student: +3%
            # - Evening/night: +2%
            is_weekend = scheduled_time.weekday() >= 5
            is_evening = scheduled_time.hour >= 18
            
            prob = base_prob
            if is_weekend:
                prob += 0.05
            if is_evening:
                prob += 0.02
            
            # Add noise
            prob += np.random.normal(0, 0.05)
            prob = max(0, min(1, prob))
            
            # Determine label: reschedule if prob > threshold
            threshold = target_reschedule_rate + 0.05  # Allow some variance
            label = 1.0 if prob > threshold else 0.0
            
            if label == 1.0:
                reschedule_count += 1
            
            # Store features in consistent order (use sorted feature names)
            if i == 0:
                feature_names = sorted(features.keys())
            X_data.append([features[name] for name in feature_names])
            y_data.append(label)
            
            if (i + 1) % 100 == 0:
                current_rate = reschedule_count / (i + 1)
                print(f"  Generated {i + 1}/{num_samples} samples... (reschedule rate: {current_rate:.1%})")
        
        except Exception as e:
            print(f"  ⚠️  Error generating sample {i}: {e}")
            continue
    
    if len(X_data) == 0:
        print("❌ No valid training samples generated")
        return None, None, None
    
    X = np.array(X_data)
    y = np.array(y_data)
    # feature_names should have been set in first iteration, otherwise use feature_names_set
    if feature_names is None:
        feature_names = sorted(feature_names_set)
    
    actual_reschedule_rate = np.mean(y)
    
    print(f"\nSynthetic data statistics:")
    print(f"  Total samples: {len(X_data)}")
    print(f"  Reschedule labels: {reschedule_count} ({actual_reschedule_rate:.1%})")
    print(f"  No-reschedule labels: {len(X_data) - reschedule_count} ({1-actual_reschedule_rate:.1%})")
    print(f"  Feature count: {len(feature_names)}")
    
    return X, y, feature_names


def train_model(X: np.ndarray, y: np.ndarray, feature_names: list):
    """
    Train XGBoost model and evaluate performance.
    
    Args:
        X: Feature matrix
        y: Labels
        feature_names: List of feature names
        
    Returns:
        Tuple of (model, feature_names, metrics, reschedule_rate)
    """
    print("\nTraining model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"  Training set: {len(X_train)} samples")
    print(f"  Test set: {len(X_test)} samples")
    
    # Calculate class weights for imbalance handling
    scale_pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1]) if len(y_train[y_train == 1]) > 0 else 1.0
    sample_weights = compute_sample_weight('balanced', y_train)
    
    print(f"  Class imbalance ratio: {scale_pos_weight:.2f}:1")
    
    # Initialize model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss',
        scale_pos_weight=scale_pos_weight
    )
    
    # Train model
    model.fit(X_train, y_train, sample_weight=sample_weights)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0.0
    
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
    
    reschedule_rate = float(np.mean(y))
    return model, feature_names, metrics, reschedule_rate


def save_model(model, feature_names: list, metrics: dict, reschedule_rate: float, model_dir: Path):
    """
    Save model and metadata to disk.
    
    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        metrics: Performance metrics
        reschedule_rate: Actual reschedule rate in training data
        model_dir: Directory to save model files
    """
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = model_dir / 'reschedule_model.pkl'
    joblib.dump(model, model_path)
    print(f"\nModel saved to: {model_path}")
    
    # Save feature names
    feature_names_path = model_dir / 'reschedule_feature_names.json'
    with open(feature_names_path, 'w') as f:
        json.dump(feature_names, f, indent=2)
    print(f"Feature names saved to: {feature_names_path}")
    
    # Save metadata
    metadata = {
        'model_version': 'v1.0',
        'trained_at': datetime.utcnow().isoformat(),
        'metrics': metrics,
        'feature_count': len(feature_names),
        'training_samples': len(model.feature_importances_),
        'reschedule_rate': reschedule_rate,
    }
    metadata_path = model_dir / 'reschedule_model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")


def main():
    """Main training function."""
    print("=" * 60)
    print("Reschedule Prediction Model Training")
    print("=" * 60)
    
    # Get model directory
    backend_dir = Path(__file__).parent.parent / 'backend'
    model_dir = backend_dir / 'models'
    
    # Try to extract historical data first
    db = SessionLocal()
    try:
        X, y, feature_names = extract_historical_training_data(db, min_sessions=100)
    except Exception as e:
        print(f"Error extracting historical data: {e}")
        X, y, feature_names = None, None, None
    finally:
        db.close()
    
    # Fallback to synthetic data if insufficient historical data
    if X is None or y is None:
        print("\nUsing synthetic data generation...")
        X, y, feature_names = generate_synthetic_training_data(
            num_samples=1000,
            target_reschedule_rate=0.12  # 12% realistic reschedule rate (aligned with data generation)
        )
    
    if X is None or y is None:
        print("❌ Failed to generate training data")
        sys.exit(1)
    
    # Train model
    model, feature_names, metrics, reschedule_rate = train_model(X, y, feature_names)
    
    # Save model
    save_model(model, feature_names, metrics, reschedule_rate, model_dir)
    
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

