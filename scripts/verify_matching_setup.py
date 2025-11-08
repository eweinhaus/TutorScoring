#!/usr/bin/env python3
"""
Verification script for Matching Service setup.
Checks all prerequisites and components are properly configured.
"""
import sys
import os
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

def check_mark(condition, message):
    """Print checkmark or X based on condition."""
    symbol = "✓" if condition else "✗"
    status = "PASS" if condition else "FAIL"
    print(f"  {symbol} {message} [{status}]")
    return condition

def main():
    print("🔍 Verifying Matching Service Setup...")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Check directory structure
    print("\n📁 Directory Structure:")
    dirs_to_check = [
        (backend_dir / "models", "backend/models/"),
        (backend_dir / "app" / "models", "backend/app/models/"),
        (project_root / "frontend" / "src" / "components" / "matching", "frontend/src/components/matching/"),
    ]
    
    for dir_path, name in dirs_to_check:
        exists = dir_path.exists() and dir_path.is_dir()
        all_passed = check_mark(exists, f"{name} directory exists") and all_passed
    
    # 2. Check Python dependencies
    print("\n📦 Python Dependencies:")
    packages = ["xgboost", "sklearn", "pandas", "numpy", "joblib", "openai"]
    for package in packages:
        try:
            __import__(package)
            all_passed = check_mark(True, f"{package} installed") and all_passed
        except ImportError:
            all_passed = check_mark(False, f"{package} installed") and all_passed
    
    # 3. Check environment variables
    print("\n🔐 Environment Variables:")
    from dotenv import load_dotenv
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    all_passed = check_mark(bool(openai_key), "OPENAI_API_KEY set") and all_passed
    
    threshold_low = os.getenv("MATCH_RISK_THRESHOLD_LOW", "0.3")
    threshold_high = os.getenv("MATCH_RISK_THRESHOLD_HIGH", "0.7")
    print(f"  ℹ️  Risk thresholds: Low={threshold_low}, High={threshold_high}")
    
    # 4. Check model files
    print("\n🤖 Model Files:")
    model_file = backend_dir / "models" / "match_model.pkl"
    feature_file = backend_dir / "models" / "feature_names.json"
    metadata_file = backend_dir / "models" / "model_metadata.json"
    
    all_passed = check_mark(model_file.exists(), "match_model.pkl exists") and all_passed
    all_passed = check_mark(feature_file.exists(), "feature_names.json exists") and all_passed
    all_passed = check_mark(metadata_file.exists(), "model_metadata.json exists") and all_passed
    
    # 5. Check database models
    print("\n🗄️  Database Models:")
    try:
        from app.models import Student, MatchPrediction
        all_passed = check_mark(True, "Student model importable") and all_passed
        all_passed = check_mark(True, "MatchPrediction model importable") and all_passed
    except ImportError as e:
        all_passed = check_mark(False, f"Models importable: {e}") and all_passed
    
    # 6. Check API router
    print("\n🌐 API Router:")
    try:
        from app.api import matching
        all_passed = check_mark(True, "matching router importable") and all_passed
    except ImportError:
        all_passed = check_mark(False, "matching router importable") and all_passed
    
    # 7. Check services
    print("\n⚙️  Services:")
    services = [
        ("feature_engineering", "Feature Engineering Service"),
        ("match_prediction_service", "Match Prediction Service"),
        ("ai_explanation_service", "AI Explanation Service"),
    ]
    
    for service_name, display_name in services:
        service_file = backend_dir / "app" / "services" / f"{service_name}.py"
        all_passed = check_mark(service_file.exists(), f"{display_name} exists") and all_passed
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! Matching Service is ready.")
        return 0
    else:
        print("❌ Some checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())


