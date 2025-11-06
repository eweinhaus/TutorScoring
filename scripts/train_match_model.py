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


def generate_synthetic_training_data(num_samples: int = 5000, target_churn_rate: float = 0.33) -> tuple:
    """
    Generate synthetic training data for model training.
    
    Uses realistic churn distribution: ~30-35% of first-session matches have churn risk.
    This reflects industry standards for first-session churn in tutoring/education platforms,
    where initial matches have higher churn rates due to compatibility issues, expectations,
    and the two-sided marketplace nature of the service.
    
    NOTE: Currently uses synthetic data. To train on real historical churn data:
    1. Track actual churn outcomes (student-tutor pairs that resulted in churn)
    2. Query MatchPrediction table with actual outcomes
    3. Use real features and actual churn labels from database
    
    Args:
        num_samples: Number of student-tutor pairs to generate (default 5000 for better generalization)
        target_churn_rate: Target churn rate (default 0.33 = 33% for first sessions)
        
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
        # Strategy: Use a threshold that results in ~33% churn rate for first sessions
        # First sessions have higher churn due to initial compatibility issues,
        # unmet expectations, and the two-sided marketplace nature
        
        # Churn probability: inverse of compatibility with realistic noise
        churn_prob = 1.0 - compatibility
        
        # Add realistic noise (higher variance for first-session uncertainty)
        churn_prob += np.random.normal(0, 0.12)
        churn_prob = max(0, min(1, churn_prob))
        
        # Use adaptive threshold based on target churn rate
        # For ~33% churn, we need threshold around 0.60-0.70
        # This means moderate-to-poor matches (compatibility < 0.30-0.40) can churn
        # Threshold: inverse of target churn rate, adjusted for noise
        # Higher threshold = fewer churn labels
        threshold = 1.0 - target_churn_rate - 0.05  # ~0.62 for 33% target (accounts for noise)
        
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
    Train XGBoost model with regularization to prevent overfitting.
    
    Args:
        X: Feature matrix
        y: Labels
        feature_names: List of feature names
        
    Returns:
        Tuple of (model, feature_names, metrics)
    """
    print("\nTraining model with anti-overfitting measures...")
    
    # Split data: train (60%), validation (20%), test (20%)
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp  # 0.25 of 0.8 = 0.2
    )
    
    print(f"  Training set: {len(X_train)} samples")
    print(f"  Validation set: {len(X_val)} samples (for early stopping)")
    print(f"  Test set: {len(X_test)} samples")
    
    # Calculate class weights for balanced learning
    # With ~33% churn, classes are more balanced than before
    sample_weights = compute_sample_weight('balanced', y_train)
    scale_pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1]) if len(y_train[y_train == 1]) > 0 else 1.0
    # Cap scale_pos_weight to avoid over-suppression
    scale_pos_weight = min(scale_pos_weight, 3.0)
    
    print(f"  Class imbalance ratio: {scale_pos_weight:.2f}:1")
    
    # Initialize base model with strong regularization to prevent overfitting
    # For XGBoost 2.0+, early_stopping_rounds goes in constructor
    base_model = xgb.XGBClassifier(
        n_estimators=300,  # More trees but with early stopping
        max_depth=3,  # Reduced from 5 to prevent overfitting
        learning_rate=0.05,  # Lower learning rate for better generalization
        min_child_weight=3,  # Increased regularization (minimum samples in leaf)
        gamma=0.1,  # Minimum loss reduction (regularization)
        subsample=0.8,  # Row sampling (80% of rows per tree)
        colsample_bytree=0.8,  # Column sampling (80% of features per tree)
        reg_alpha=0.1,  # L1 regularization
        reg_lambda=1.0,  # L2 regularization
        random_state=42,
        eval_metric='logloss',
        scale_pos_weight=scale_pos_weight,
        tree_method='hist',  # Faster training
        early_stopping_rounds=20  # Stop if no improvement for 20 rounds (XGBoost 2.0+)
    )
    
    print("\n  Training with early stopping to prevent overfitting...")
    # Train base model with early stopping on validation set
    base_model.fit(
        X_train, y_train,
        sample_weight=sample_weights,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False
    )
    
    # Get best iteration (XGBoost 2.0+ stores this differently)
    best_iteration = getattr(base_model, 'best_iteration', base_model.n_estimators)
    best_score = getattr(base_model, 'best_score', None)
    if best_score is None:
        # Try to get from evaluation results
        evals_result = getattr(base_model, 'evals_result_', {})
        if evals_result:
            val_key = list(evals_result.keys())[-1] if evals_result else None
            if val_key and 'validation_1' in str(val_key):
                best_score = min(evals_result.get('validation_1', {}).get('logloss', [0]))
    
    print(f"  Best iteration: {best_iteration}/{base_model.n_estimators}")
    if best_score:
        print(f"  Best validation score: {best_score:.4f}")
    
    # Create a new model for calibration without early stopping
    # (CalibratedClassifierCV needs to refit during cross-validation)
    print("\nCalibrating model probabilities...")
    print("  Using isotonic regression to improve probability calibration")
    
    # Create a fresh model with same parameters but without early stopping for calibration
    base_model_for_calibration = xgb.XGBClassifier(
        n_estimators=best_iteration if best_iteration < base_model.n_estimators else base_model.n_estimators,
        max_depth=base_model.max_depth,
        learning_rate=base_model.learning_rate,
        min_child_weight=base_model.min_child_weight,
        gamma=base_model.gamma,
        subsample=base_model.subsample,
        colsample_bytree=base_model.colsample_bytree,
        reg_alpha=base_model.reg_alpha,
        reg_lambda=base_model.reg_lambda,
        random_state=base_model.random_state,
        eval_metric=base_model.eval_metric,
        scale_pos_weight=base_model.scale_pos_weight,
        tree_method=base_model.tree_method,
        # No early_stopping_rounds for calibration
    )
    
    # Use combined train+val for calibration to maximize data usage
    X_train_val = np.vstack([X_train, X_val])
    y_train_val = np.concatenate([y_train, y_val])
    
    # Fit the calibration model on combined data
    base_model_for_calibration.fit(X_train_val, y_train_val, sample_weight=compute_sample_weight('balanced', y_train_val))
    
    # Now calibrate
    model = CalibratedClassifierCV(
        base_model_for_calibration,
        method='isotonic',  # Use isotonic regression for better calibration
        cv=3,  # 3-fold cross-validation for calibration
        n_jobs=-1
    )
    model.fit(X_train_val, y_train_val)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Check calibration and distribution before/after
    print("\nChecking probability calibration and distribution...")
    # Get uncalibrated predictions for comparison
    y_pred_proba_uncalibrated = base_model.predict_proba(X_test)[:, 1]
    
    # Calculate calibration metrics
    def count_extreme_probs(probs, threshold_low=0.01, threshold_high=0.9):
        """Count extremely confident predictions."""
        very_low = sum(1 for p in probs if p < threshold_low)
        very_high = sum(1 for p in probs if p >= threshold_high)
        return very_low, very_high
    
    def get_prob_stats(probs):
        """Get probability distribution statistics."""
        return {
            'mean': np.mean(probs),
            'median': np.median(probs),
            'min': np.min(probs),
            'max': np.max(probs),
            'std': np.std(probs),
            'percentile_25': np.percentile(probs, 25),
            'percentile_75': np.percentile(probs, 75),
        }
    
    uncal_low, uncal_high = count_extreme_probs(y_pred_proba_uncalibrated)
    cal_low, cal_high = count_extreme_probs(y_pred_proba)
    
    uncal_stats = get_prob_stats(y_pred_proba_uncalibrated)
    cal_stats = get_prob_stats(y_pred_proba)
    
    print(f"  Uncalibrated - Very low (<1%): {uncal_low}/{len(y_test)} ({uncal_low/len(y_test)*100:.1f}%)")
    print(f"  Uncalibrated - Very high (>=90%): {uncal_high}/{len(y_test)} ({uncal_high/len(y_test)*100:.1f}%)")
    print(f"  Uncalibrated - Mean: {uncal_stats['mean']:.3f}, Median: {uncal_stats['median']:.3f}")
    print(f"  Calibrated - Very low (<1%): {cal_low}/{len(y_test)} ({cal_low/len(y_test)*100:.1f}%)")
    print(f"  Calibrated - Very high (>=90%): {cal_high}/{len(y_test)} ({cal_high/len(y_test)*100:.1f}%)")
    print(f"  Calibrated - Mean: {cal_stats['mean']:.3f}, Median: {cal_stats['median']:.3f}")
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    # Check for overfitting: compare train vs test performance
    y_pred_train = model.predict(X_train)
    y_pred_proba_train = model.predict_proba(X_train)[:, 1]
    train_accuracy = accuracy_score(y_train, y_pred_train)
    train_roc_auc = roc_auc_score(y_train, y_pred_proba_train)
    
    print(f"\n  Overfitting check:")
    print(f"    Train accuracy: {train_accuracy:.4f}")
    print(f"    Test accuracy:  {accuracy:.4f}")
    print(f"    Difference:     {train_accuracy - accuracy:.4f} (should be < 0.10)")
    print(f"    Train ROC-AUC:   {train_roc_auc:.4f}")
    print(f"    Test ROC-AUC:    {roc_auc:.4f}")
    print(f"    Difference:      {train_roc_auc - roc_auc:.4f} (should be < 0.10)")
    
    if train_accuracy - accuracy > 0.10:
        print(f"    ⚠️  Warning: Large train-test gap suggests overfitting!")
    if train_roc_auc - roc_auc > 0.10:
        print(f"    ⚠️  Warning: Large ROC-AUC gap suggests overfitting!")
    
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
        'model_version': 'v2.0',  # Updated version for realistic churn rate and anti-overfitting
        'trained_at': datetime.utcnow().isoformat(),
        'metrics': metrics,
        'feature_count': len(feature_names),
        'calibrated': True,  # Mark that this model is calibrated
        'calibration_method': 'isotonic',
        'target_churn_rate': 0.33,  # Realistic first-session churn rate
        'regularization': {
            'max_depth': 3,
            'min_child_weight': 3,
            'gamma': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
        },
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
    
    # Generate training data with realistic ~33% churn rate for first sessions
    # Industry standards show 25-45% first-session churn for tutoring platforms
    # This reflects the two-sided marketplace nature and initial compatibility issues
    # Using 33% as a balanced middle ground
    X, y, feature_names = generate_synthetic_training_data(
        num_samples=5000,  # Increased for better generalization
        target_churn_rate=0.33  # 33% realistic first-session churn rate
    )
    
    # Train model
    model, feature_names, metrics = train_model(X, y, feature_names)
    
    # Save model
    save_model(model, feature_names, metrics, model_dir)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)
    
    # Check if metrics meet thresholds
    print("\n" + "=" * 60)
    print("Model Quality Checks:")
    print("=" * 60)
    
    if metrics['precision'] < 0.60:
        print(f"⚠️  Warning: Precision ({metrics['precision']:.4f}) is below 0.60 threshold.")
        print("   Consider increasing training data or tuning hyperparameters.")
    else:
        print(f"✅ Model precision ({metrics['precision']:.4f}) meets 0.60 threshold.")
    
    if metrics['recall'] < 0.50:
        print(f"⚠️  Warning: Recall ({metrics['recall']:.4f}) is below 0.50 threshold.")
        print("   Model may be missing too many churn cases.")
    else:
        print(f"✅ Model recall ({metrics['recall']:.4f}) meets 0.50 threshold.")
    
    if metrics['roc_auc'] < 0.75:
        print(f"⚠️  Warning: ROC-AUC ({metrics['roc_auc']:.4f}) is below 0.75 threshold.")
    else:
        print(f"✅ Model ROC-AUC ({metrics['roc_auc']:.4f}) meets 0.75 threshold.")
    
    # Check for overfitting indicators
    if metrics['accuracy'] > 0.95:
        print(f"⚠️  Warning: Very high accuracy ({metrics['accuracy']:.4f}) may indicate overfitting.")
        print("   Monitor validation performance closely.")
    else:
        print(f"✅ Model accuracy ({metrics['accuracy']:.4f}) is reasonable (not suspiciously high).")


if __name__ == '__main__':
    main()

