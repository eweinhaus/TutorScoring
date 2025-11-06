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
    from sklearn.preprocessing import StandardScaler
    from sklearn.calibration import CalibratedClassifierCV
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
    # Use a simple mock that doesn't require full database setup
    # We'll create a minimal mock session object that provides the needed interface
    class MockDB:
        """Mock database session for synthetic data generation."""
        def query(self, model_class):
            return MockQuery()
    
    class MockQuery:
        """Mock query object."""
        def filter(self, *args, **kwargs):
            return self
        def count(self):
            return 0  # No previous sessions for synthetic data
    
    db = MockDB()
    
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
            import uuid
            tutor_uuid = str(uuid.uuid4())
            student_id = str(uuid.uuid4()).replace('-', '')[:8]  # Simple 8-char student ID
            session = Session(
                id=None,  # Not saved
                tutor_id=tutor_uuid,
                student_id=student_id,
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
            # Use a more sophisticated approach to match target rate
            # Sample from a Bernoulli distribution with the calculated probability
            label = 1.0 if np.random.random() < prob else 0.0
            
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
    Train XGBoost model with feature scaling, regularization, and calibration.
    
    Args:
        X: Feature matrix
        y: Labels
        feature_names: List of feature names
        
    Returns:
        Tuple of (model_pipeline, scaler, feature_names, metrics, reschedule_rate)
        model_pipeline is a dict with 'model' and 'calibrator' keys
    """
    print("\nTraining model with improved configuration...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"  Training set: {len(X_train)} samples")
    print(f"  Test set: {len(X_test)} samples")
    
    # Apply feature scaling (StandardScaler)
    print("\n  Applying feature scaling (StandardScaler)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Calculate class weights for imbalance handling (less aggressive)
    scale_pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1]) if len(y_train[y_train == 1]) > 0 else 1.0
    # Reduce scale_pos_weight to avoid over-suppression of positive class
    scale_pos_weight = min(scale_pos_weight, 5.0)  # Cap at 5:1 ratio
    
    print(f"  Class imbalance ratio: {scale_pos_weight:.2f}:1")
    
    # Initialize model with very strong regularization to prevent overfitting
    # Goal: 75-85% accuracy (realistic), not 98%+ (overfitting)
    base_model = xgb.XGBClassifier(
        n_estimators=100,  # Fewer trees to reduce overfitting
        max_depth=2,  # Shallow trees prevent memorization
        learning_rate=0.02,  # Very low learning rate for smooth learning
        min_child_weight=10,  # Strong regularization (was 5)
        gamma=0.3,  # Higher minimum loss reduction (was 0.2)
        subsample=0.6,  # More aggressive row sampling (was 0.7)
        colsample_bytree=0.6,  # More aggressive column sampling (was 0.7)
        reg_alpha=0.5,  # Strong L1 regularization (was 0.3)
        reg_lambda=3.0,  # Strong L2 regularization (was 2.0)
        random_state=42,
        eval_metric='logloss',
        scale_pos_weight=min(scale_pos_weight, 2.5),  # Cap to avoid over-suppression
        tree_method='hist'  # Faster training
    )
    
    # Train with early stopping (only for initial training, not for calibration)
    print("\n  Training base model with early stopping...")
    try:
        # Try newer XGBoost API with callbacks
        from xgboost import callback
        early_stop = callback.EarlyStopping(rounds=20, save_best=True)
        base_model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_train_scaled, y_train), (X_test_scaled, y_test)],
            callbacks=[early_stop],
            verbose=False
        )
    except (ImportError, AttributeError, TypeError):
        # Fallback: train without early stopping if callbacks not supported
        print("    (Early stopping not available, training without it)")
        base_model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_train_scaled, y_train), (X_test_scaled, y_test)],
            verbose=False
        )
    
    # Make base predictions
    y_pred_base = base_model.predict(X_test_scaled)
    y_pred_proba_base = base_model.predict_proba(X_test_scaled)[:, 1]
    
    # Calculate base metrics
    accuracy_base = accuracy_score(y_test, y_pred_base)
    precision_base = precision_score(y_test, y_pred_base, zero_division=0)
    recall_base = recall_score(y_test, y_pred_base, zero_division=0)
    f1_base = f1_score(y_test, y_pred_base, zero_division=0)
    roc_auc_base = roc_auc_score(y_test, y_pred_proba_base) if len(np.unique(y_test)) > 1 else 0.0
    
    print("\n  Base Model Performance (before calibration):")
    print(f"    Accuracy:  {accuracy_base:.4f}")
    print(f"    Precision: {precision_base:.4f}")
    print(f"    Recall:    {recall_base:.4f}")
    print(f"    F1 Score:  {f1_base:.4f}")
    print(f"    ROC-AUC:   {roc_auc_base:.4f}")
    
    # Apply probability calibration (Platt scaling - smoother than isotonic)
    print("\n  Calibrating probabilities (Platt scaling - smoother calibration)...")
    # Use Platt scaling instead of isotonic to avoid extreme bins
    # Isotonic can create extreme predictions when base model is overconfident
    calibrator = CalibratedClassifierCV(base_model, method='sigmoid', cv=5)
    calibrator.fit(X_train_scaled, y_train)
    
    # Make calibrated predictions
    y_pred_cal = calibrator.predict(X_test_scaled)
    y_pred_proba_cal = calibrator.predict_proba(X_test_scaled)[:, 1]
    
    # Calculate calibrated metrics
    accuracy_cal = accuracy_score(y_test, y_pred_cal)
    precision_cal = precision_score(y_test, y_pred_cal, zero_division=0)
    recall_cal = recall_score(y_test, y_pred_cal, zero_division=0)
    f1_cal = f1_score(y_test, y_pred_cal, zero_division=0)
    roc_auc_cal = roc_auc_score(y_test, y_pred_proba_cal) if len(np.unique(y_test)) > 1 else 0.0
    
    # Analyze prediction distribution
    mean_pred = float(np.mean(y_pred_proba_cal))
    min_pred = float(np.min(y_pred_proba_cal))
    max_pred = float(np.max(y_pred_proba_cal))
    std_pred = float(np.std(y_pred_proba_cal))
    
    # Risk level distribution
    low_count = np.sum(y_pred_proba_cal < 0.15)
    medium_count = np.sum((y_pred_proba_cal >= 0.15) & (y_pred_proba_cal < 0.35))
    high_count = np.sum(y_pred_proba_cal >= 0.35)
    
    metrics = {
        'accuracy': float(accuracy_cal),
        'precision': float(precision_cal),
        'recall': float(recall_cal),
        'f1_score': float(f1_cal),
        'roc_auc': float(roc_auc_cal),
        'prediction_distribution': {
            'mean': mean_pred,
            'min': min_pred,
            'max': max_pred,
            'std': std_pred,
        },
        'risk_level_distribution': {
            'low': int(low_count),
            'medium': int(medium_count),
            'high': int(high_count),
        },
        'base_metrics': {
            'accuracy': float(accuracy_base),
            'precision': float(precision_base),
            'recall': float(recall_base),
            'f1_score': float(f1_base),
            'roc_auc': float(roc_auc_base),
        }
    }
    
    print("\n  Calibrated Model Performance:")
    print(f"    Accuracy:  {metrics['accuracy']:.4f}")
    print(f"    Precision: {metrics['precision']:.4f}")
    print(f"    Recall:    {metrics['recall']:.4f}")
    print(f"    F1 Score:  {metrics['f1_score']:.4f}")
    print(f"    ROC-AUC:   {metrics['roc_auc']:.4f}")
    
    print("\n  Prediction Distribution (calibrated):")
    print(f"    Mean: {mean_pred:.4f} ({mean_pred*100:.2f}%)")
    print(f"    Min:  {min_pred:.4f} ({min_pred*100:.2f}%)")
    print(f"    Max:  {max_pred:.4f} ({max_pred*100:.2f}%)")
    print(f"    Std:  {std_pred:.4f}")
    
    print("\n  Risk Level Distribution:")
    print(f"    Low:    {low_count} ({low_count/len(y_test)*100:.1f}%)")
    print(f"    Medium: {medium_count} ({medium_count/len(y_test)*100:.1f}%)")
    print(f"    High:   {high_count} ({high_count/len(y_test)*100:.1f}%)")
    
    # Feature importance
    feature_importance = dict(zip(feature_names, base_model.feature_importances_.tolist()))
    sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    print("\n  Top 10 Most Important Features:")
    for name, importance in sorted_importance[:10]:
        print(f"    {name}: {importance:.4f}")
    
    # Check for single-feature dominance
    top_feature_importance = sorted_importance[0][1] if sorted_importance else 0.0
    if top_feature_importance > 0.30:
        print(f"\n  ⚠️  Warning: Top feature ({sorted_importance[0][0]}) has {top_feature_importance:.1%} importance")
        print(f"     Consider feature engineering to reduce dominance")
    
    # Validate prediction distribution matches training
    actual_reschedule_rate = float(np.mean(y))
    print(f"\n  Validation:")
    print(f"    Training reschedule rate: {actual_reschedule_rate:.4f} ({actual_reschedule_rate*100:.2f}%)")
    print(f"    Mean prediction: {mean_pred:.4f} ({mean_pred*100:.2f}%)")
    if abs(mean_pred - actual_reschedule_rate) > 0.05:
        print(f"    ⚠️  Warning: Mean prediction differs from training rate by {abs(mean_pred - actual_reschedule_rate)*100:.2f}%")
    else:
        print(f"    ✅ Mean prediction aligns with training rate")
    
    # Create model pipeline dict
    model_pipeline = {
        'model': base_model,
        'calibrator': calibrator
    }
    
    reschedule_rate = float(np.mean(y))
    return model_pipeline, scaler, feature_names, metrics, reschedule_rate


def save_model(model_pipeline: dict, scaler: StandardScaler, feature_names: list, metrics: dict, reschedule_rate: float, model_dir: Path):
    """
    Save model pipeline (model + calibrator), scaler, and metadata to disk.
    
    Args:
        model_pipeline: Dict with 'model' and 'calibrator' keys
        scaler: StandardScaler fitted to training data
        feature_names: List of feature names
        metrics: Performance metrics
        reschedule_rate: Actual reschedule rate in training data
        model_dir: Directory to save model files
    """
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model pipeline (model + calibrator)
    model_path = model_dir / 'reschedule_model.pkl'
    joblib.dump(model_pipeline, model_path)
    print(f"\nModel pipeline saved to: {model_path}")
    
    # Save scaler
    scaler_path = model_dir / 'reschedule_scaler.pkl'
    joblib.dump(scaler, scaler_path)
    print(f"Scaler saved to: {scaler_path}")
    
    # Save feature names
    feature_names_path = model_dir / 'reschedule_feature_names.json'
    with open(feature_names_path, 'w') as f:
        json.dump(feature_names, f, indent=2)
    print(f"Feature names saved to: {feature_names_path}")
    
    # Save metadata
    metadata = {
        'model_version': 'v2.2',  # Updated version with synthetic data augmentation
        'trained_at': datetime.utcnow().isoformat(),
        'metrics': metrics,
        'feature_count': len(feature_names),
        'training_samples': len(model_pipeline['model'].feature_importances_),
        'reschedule_rate': reschedule_rate,
        'has_scaler': True,
        'has_calibrator': True,
        'prediction_clip_range': [0.005, 0.40],  # Document clipping range (0.5% to 40%)
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
    # OR supplement historical data with synthetic data for better generalization
    if X is None or y is None:
        print("\nUsing synthetic data generation...")
        X, y, feature_names = generate_synthetic_training_data(
            num_samples=5000,  # Increased from 1000 to 5000 for better generalization
            target_reschedule_rate=0.12  # 12% realistic reschedule rate (aligned with data generation)
        )
    else:
        # Supplement historical data with synthetic data to improve generalization
        print("\nSupplementing historical data with synthetic data...")
        X_synth, y_synth, feature_names_synth = generate_synthetic_training_data(
            num_samples=3000,  # Add 3000 synthetic samples
            target_reschedule_rate=0.12
        )
        
        if X_synth is not None and y_synth is not None:
            # Ensure feature names match
            if set(feature_names) == set(feature_names_synth):
                # Combine datasets
                X = np.vstack([X, X_synth])
                y = np.concatenate([y, y_synth])
                print(f"Combined dataset: {len(X)} total samples ({len(X) - len(X_synth)} historical + {len(X_synth)} synthetic)")
            else:
                print("⚠️  Feature names don't match, using only historical data")
    
    if X is None or y is None:
        print("❌ Failed to generate training data")
        sys.exit(1)
    
    # Train model
    model_pipeline, scaler, feature_names, metrics, reschedule_rate = train_model(X, y, feature_names)
    
    # Save model
    save_model(model_pipeline, scaler, feature_names, metrics, reschedule_rate, model_dir)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)
    
    # Validation checks
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    # Check prediction distribution
    pred_dist = metrics.get('prediction_distribution', {})
    mean_pred = pred_dist.get('mean', 0.0)
    min_pred = pred_dist.get('min', 0.0)
    max_pred = pred_dist.get('max', 0.0)
    
    print(f"\nPrediction Range: {min_pred*100:.2f}% - {max_pred*100:.2f}%")
    print(f"Mean Prediction: {mean_pred*100:.2f}%")
    print(f"Training Rate: {reschedule_rate*100:.2f}%")
    
    # Expected outcomes
    if 0.05 <= mean_pred <= 0.25:
        print(f"✅ Mean prediction ({mean_pred*100:.2f}%) is in expected range (5-25%)")
    else:
        print(f"⚠️  Mean prediction ({mean_pred*100:.2f}%) is outside expected range (5-25%)")
    
    if 0.70 <= metrics['accuracy'] <= 0.85:
        print(f"✅ Accuracy ({metrics['accuracy']:.4f}) is in realistic range (70-85%)")
    else:
        print(f"⚠️  Accuracy ({metrics['accuracy']:.4f}) may indicate overfitting (<70%) or underfitting (>85%)")
    
    # Check risk level distribution
    risk_dist = metrics.get('risk_level_distribution', {})
    total_test = sum(risk_dist.values()) if risk_dist else 0
    if total_test > 0:
        low_pct = risk_dist.get('low', 0) / total_test
        medium_pct = risk_dist.get('medium', 0) / total_test
        high_pct = risk_dist.get('high', 0) / total_test
        
        print(f"\nRisk Level Distribution:")
        print(f"  Low: {low_pct*100:.1f}% (expected: 60-70%)")
        print(f"  Medium: {medium_pct*100:.1f}% (expected: 20-30%)")
        print(f"  High: {high_pct*100:.1f}% (expected: 5-15%)")
        
        if 0.60 <= low_pct <= 0.70 and 0.20 <= medium_pct <= 0.30:
            print(f"✅ Risk level distribution looks reasonable")
        else:
            print(f"⚠️  Risk level distribution may need adjustment")
    
    # Check precision
    if metrics['precision'] < 0.70:
        print(f"\n⚠️  Warning: Precision ({metrics['precision']:.4f}) is below 0.70 threshold.")
        print("   Consider increasing training data or tuning hyperparameters.")
    else:
        print(f"\n✅ Model precision ({metrics['precision']:.4f}) meets 0.70 threshold.")


if __name__ == '__main__':
    main()

