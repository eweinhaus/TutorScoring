# Matching Service Documentation

## Overview

The Matching Service predicts student-tutor compatibility and churn risk to help reduce the 24% of churners who fail at the first session stage. It uses machine learning (XGBoost) to predict churn probability and provides AI-powered explanations for match quality.

## Features

- **Student Profile Management**: Store student preferences and demographics
- **Tutor Preference Enhancement**: Extend existing tutors with matching preferences
- **ML-Powered Predictions**: XGBoost model predicts churn probability
- **Compatibility Scoring**: Calculate mismatch scores and compatibility
- **AI Explanations**: GPT-4 generates natural language explanations
- **Interactive Dashboard**: Frontend interface for exploring matches

## Architecture

### Database Schema

**Students Table:**
- `id` (UUID, PK)
- `name`, `age`, `sex`
- `preferred_pace` (1-5 scale)
- `preferred_teaching_style` (structured, flexible, interactive, etc.)
- `communication_style_preference` (1-5 scale)
- `urgency_level` (1-5 scale)
- `learning_goals`, `previous_tutoring_experience`, `previous_satisfaction`
- `preferences_json` (flexible JSON field)
- `created_at`, `updated_at`

**Tutors Table (Extended):**
- Existing fields: `id`, `name`, `email`, `is_active`
- **New fields (all nullable):**
  - `age`, `sex`, `experience_years`
  - `teaching_style`, `preferred_pace`, `communication_style`
  - `confidence_level`, `preferred_student_level`
  - `preferences_json`

**Match Predictions Table:**
- `id` (UUID, PK)
- `student_id` (FK → students)
- `tutor_id` (FK → tutors)
- `churn_probability` (0-1)
- `risk_level` (low, medium, high)
- `compatibility_score` (0-1)
- `pace_mismatch`, `style_mismatch`, `communication_mismatch`, `age_difference`
- `ai_explanation` (TEXT, cached)
- `model_version`
- Unique constraint on (student_id, tutor_id)
- `created_at`, `updated_at`

### ML Model

**Model Type:** XGBoost Binary Classifier  
**Purpose:** Predict churn probability (0-1)  
**Features:**
- Mismatch scores (pace, style, communication, age)
- Student demographics and preferences
- Tutor experience and preferences
- Tutor statistics (reschedule rates, risk flags)

**Training:**
- Synthetic data generation (1000+ samples)
- 80/20 train/test split
- 5-fold cross-validation
- Target: >70% precision

**Model Files:**
- `backend/models/match_model.pkl` - Trained model
- `backend/models/feature_names.json` - Feature names
- `backend/models/model_metadata.json` - Version and metrics

### API Endpoints

**Base URL:** `/api/matching`

#### Student Endpoints

- `GET /students` - List students (paginated)
- `GET /students/{id}` - Get student details
- `POST /students` - Create new student

#### Tutor Endpoints

- `GET /tutors` - List tutors with preferences
- `GET /tutors/{id}` - Get tutor with preferences
- `PATCH /tutors/{id}` - Update tutor preferences

#### Match Prediction Endpoints

- `GET /predict/{student_id}/{tutor_id}` - Get or create match prediction
- `POST /generate-all` - Generate predictions for all pairs
- `GET /students/{id}/matches` - Get all matches for student
- `GET /tutors/{id}/matches` - Get all matches for tutor

All endpoints require `X-API-Key` header.

### Frontend Dashboard

**Route:** `/matching`

**Components:**
- `MatchingDashboard` - Main page with three-column layout
- `StudentList` - Left column with selectable students
- `TutorList` - Middle column with selectable tutors
- `MatchDetailPanel` - Right column with match details

**Features:**
- Real-time match prediction display
- Visual risk indicators (color-coded)
- Compatibility score progress bar
- Mismatch score breakdown
- AI explanation display

## Usage

### Setup

1. **Install Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run Migration:**
   ```bash
   alembic upgrade head
   ```

3. **Train Model (Optional):**
   ```bash
   python scripts/train_match_model.py
   ```
   Note: Service works without trained model (uses rule-based fallback)

4. **Generate Test Data:**
   ```bash
   python scripts/generate_matching_data.py --num-students 20 --generate-predictions
   ```

### API Usage

**Create Student:**
```bash
curl -X POST http://localhost:8001/api/matching/students \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 15,
    "preferred_pace": 3,
    "preferred_teaching_style": "structured",
    "communication_style_preference": 3,
    "urgency_level": 2
  }'
```

**Get Match Prediction:**
```bash
curl http://localhost:8001/api/matching/predict/{student_id}/{tutor_id} \
  -H "X-API-Key: your-api-key"
```

### Frontend Usage

1. Navigate to `/matching`
2. Select a student from the left column
3. Select a tutor from the middle column
4. View match details in the right panel

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Required for AI explanations (optional, has fallback)
- `MATCH_RISK_THRESHOLD_LOW` - Low risk threshold (default: 0.3)
- `MATCH_RISK_THRESHOLD_HIGH` - High risk threshold (default: 0.7)

### Risk Level Thresholds

- **Low Risk:** churn_probability < 0.3
- **Medium Risk:** 0.3 ≤ churn_probability < 0.7
- **High Risk:** churn_probability ≥ 0.7

## Performance

- **API Response Time:** <200ms (target)
- **Dashboard Load Time:** <2 seconds (target)
- **AI Explanation Generation:** <3 seconds (target)
- **Batch Prediction Generation:** ~100 predictions/second

## Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Specific matching tests
pytest tests/api/test_matching.py -v
pytest tests/services/test_feature_engineering.py -v
pytest tests/services/test_match_prediction_service.py -v
```

### Test Coverage

- API endpoint tests
- Feature engineering tests
- Match prediction service tests
- Model validation tests

## Troubleshooting

### Model Not Found

If you see "Model file not found" errors:
1. Run `python scripts/train_match_model.py` to train the model
2. Service will use rule-based fallback if model not available

### OpenAI API Errors

If AI explanations fail:
1. Check `OPENAI_API_KEY` is set
2. Service automatically falls back to rule-based explanations
3. Check API rate limits if generating many explanations

### Database Migration Issues

If migration fails:
1. Check `DATABASE_URL` is set correctly
2. Ensure database is accessible
3. Review migration file: `backend/alembic/versions/add_matching_tables.py`

## Future Enhancements

- Real-time model retraining
- Advanced feature engineering
- Multi-factor compatibility scoring
- Historical match performance tracking
- Automated match recommendations

