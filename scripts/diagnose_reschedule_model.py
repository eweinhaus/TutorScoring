"""
Diagnostic script to analyze reschedule prediction model issues.
"""
import sys
from pathlib import Path
import numpy as np
import joblib
import json

# Add backend to path
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.utils.database import SessionLocal
from app.models.session import Session as SessionModel
from app.models.session_reschedule_prediction import SessionReschedulePrediction
from app.services.reschedule_feature_engineering import extract_features
from app.services.tutor_service import get_tutor_statistics

def analyze_predictions():
    """Analyze current predictions and feature distributions."""
    print("=" * 60)
    print("Reschedule Model Diagnostic")
    print("=" * 60)
    
    # Load model
    model_path = backend_dir / 'models' / 'reschedule_model.pkl'
    feature_names_path = backend_dir / 'models' / 'reschedule_feature_names.json'
    
    model = joblib.load(model_path)
    with open(feature_names_path) as f:
        feature_names = json.load(f)
    
    print(f"\nModel Info:")
    print(f"  Classes: {model.n_classes_}")
    print(f"  Features: {len(feature_names)}")
    
    # Get sample predictions from database
    db = SessionLocal()
    try:
        predictions = db.query(SessionReschedulePrediction).limit(50).all()
        
        if not predictions:
            print("\n❌ No predictions found in database")
            return
        
        probabilities = [float(p.reschedule_probability) for p in predictions]
        
        print(f"\n📊 Prediction Statistics (sample of {len(predictions)}):")
        print(f"  Min: {min(probabilities):.4f} ({min(probabilities)*100:.2f}%)")
        print(f"  Max: {max(probabilities):.4f} ({max(probabilities)*100:.2f}%)")
        print(f"  Mean: {np.mean(probabilities):.4f} ({np.mean(probabilities)*100:.2f}%)")
        print(f"  Median: {np.median(probabilities):.4f} ({np.median(probabilities)*100:.2f}%)")
        print(f"  Std Dev: {np.std(probabilities):.4f}")
        
        # Analyze feature distributions for a sample prediction
        sample_pred = predictions[0]
        session = db.query(SessionModel).filter(
            SessionModel.id == sample_pred.session_id
        ).first()
        
        if session:
            tutor_stats = get_tutor_statistics(str(session.tutor_id), db)
            features = extract_features(session, tutor_stats, db)
            
            print(f"\n🔍 Sample Feature Values:")
            print(f"  Session: {session.id}")
            print(f"  Tutor reschedule rate (30d): {tutor_stats.get('reschedule_rate_30d', 0):.2f}%")
            print(f"  Session duration: {session.duration_minutes} minutes")
            
            # Show top features by value
            sorted_features = sorted(features.items(), key=lambda x: abs(x[1]), reverse=True)
            print(f"\n  Top 10 Features by Absolute Value:")
            for name, value in sorted_features[:10]:
                print(f"    {name}: {value:.4f}")
            
            # Check if features match model expectations
            feature_vector = np.array([[features.get(name, 0.0) for name in feature_names]])
            predicted_prob = model.predict_proba(feature_vector)[0, 1]
            
            print(f"\n  Model Prediction: {predicted_prob:.4f} ({predicted_prob*100:.2f}%)")
            print(f"  Stored Prediction: {float(sample_pred.reschedule_probability):.4f} ({float(sample_pred.reschedule_probability)*100:.2f}%)")
            
            # Check feature importance
            print(f"\n📈 Model Feature Importance (Top 5):")
            importance_dict = dict(zip(feature_names, model.feature_importances_))
            top_important = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            for name, importance in top_important:
                print(f"  {name}: {importance:.4f} ({importance*100:.2f}%)")
        
        # Check risk level distribution
        risk_levels = {}
        for p in predictions:
            risk_levels[p.risk_level] = risk_levels.get(p.risk_level, 0) + 1
        
        print(f"\n⚠️  Risk Level Distribution:")
        for level, count in sorted(risk_levels.items()):
            print(f"  {level}: {count} ({count/len(predictions)*100:.1f}%)")
        
    finally:
        db.close()

if __name__ == "__main__":
    analyze_predictions()


