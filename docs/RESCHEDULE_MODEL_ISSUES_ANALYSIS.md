# Reschedule Prediction Model Issues Analysis

## Executive Summary

**Current predictions: 0.1-2.4% (mean: 1.01%)**  
**Expected predictions: 10-15% (based on training data with 15.3% reschedule rate)**  
**Status: ❌ Model is severely miscalibrated and overfit**

## Problems Identified

### 1. ❌ Severe Feature Scaling Mismatch

**Issue:** Features are not normalized, causing the model to over-rely on large-scale features.

**Evidence:**
- `hours_until_session: 296.93` (very large scale)
- `session_duration_minutes: 90.0` (medium scale)
- `tutor_reschedule_rate_30d: 0.1538` (small scale, 0-1)
- `tutor_is_high_risk: 0.0 or 1.0` (binary)

**Impact:** XGBoost is tree-based and should handle scale differences, but the extreme feature importance imbalance suggests the model learned to use only one feature.

### 2. ❌ Extreme Overfitting

**Evidence:**
- **Accuracy: 99.16%** (suspiciously high)
- **Recall: 100%** (perfect recall = likely overfitting)
- **Precision: 94.79%** (high but still concerning)
- **Single feature dominance: 93.64%** (`session_duration_minutes`)

**Why this is bad:**
- Model memorized patterns instead of learning generalizable rules
- Won't generalize to new data distributions
- Predictions are too conservative (all low risk)

### 3. ❌ Miscalibrated Predictions

**Problem:** Model predicts 0.1-2.4% when training data had 15.3% reschedule rate.

**Possible causes:**
1. **Feature distribution mismatch**: Training features ≠ prediction features
2. **Model calibration issue**: Probabilities aren't calibrated to match training distribution
3. **Class imbalance handling**: `scale_pos_weight` might be too aggressive

### 4. ❌ Synthetic Data Not Used

**Issue:** Training used historical data (15.3% rate), but:
- Synthetic data generation exists but wasn't used
- Historical data might not represent real-world distribution
- No validation that synthetic data matches expectations

### 5. ❌ All Predictions Categorized as Low Risk

**Evidence:**
- 100% of predictions are "low" risk
- Risk thresholds: low < 15%, medium < 35%, high >= 35%
- Mean prediction: 1.01% (all below 15% threshold)

**Impact:** Dashboard can't distinguish between different risk levels.

## Root Causes

### Primary: Feature Engineering Issues

1. **No feature normalization**: Raw features with different scales (0-1 vs 0-300)
2. **Single dominant feature**: Model learned to rely almost exclusively on `session_duration_minutes`
3. **Feature distribution mismatch**: Training features may have different distributions than prediction features

### Secondary: Model Training Issues

1. **Overfitting**: 99% accuracy with 100% recall = model memorized training data
2. **Insufficient regularization**: No max_depth limits, no early stopping
3. **Class imbalance**: `scale_pos_weight` might be too high, causing conservative predictions

### Tertiary: Data Quality Issues

1. **Training data**: 2,972 samples with 15.3% reschedule rate
2. **Feature quality**: Most features have minimal signal (93.64% importance on one feature)
3. **No validation**: No hold-out validation set or cross-validation

## Recommendations

### Immediate Fixes (High Priority)

1. **✅ Retrain with proper feature scaling**
   - Normalize/standardize all features
   - Use StandardScaler or MinMaxScaler
   - Ensure same scaling in training and prediction

2. **✅ Reduce overfitting**
   - Increase regularization (higher `min_child_weight`, `gamma`)
   - Reduce `max_depth` (currently 5, try 3-4)
   - Add early stopping
   - Use cross-validation

3. **✅ Fix feature importance imbalance**
   - Investigate why `session_duration_minutes` dominates
   - Check if this feature has strong predictive signal or is just correlated
   - Consider feature engineering alternatives

4. **✅ Recalibrate model**
   - Use Platt scaling or isotonic regression
   - Ensure predicted probabilities match training distribution

### Medium-Term Improvements

1. **✅ Improve feature engineering**
   - Add more meaningful features (tutor history, student patterns)
   - Remove or transform low-signal features
   - Create interaction features

2. **✅ Better training data**
   - Use more historical data if available
   - Generate realistic synthetic data
   - Ensure training/prediction feature distributions match

3. **✅ Model validation**
   - Use time-based train/test split
   - Cross-validation
   - Monitor prediction distribution over time

### Long-Term Improvements

1. **✅ Model monitoring**
   - Track prediction distributions
   - Alert if predictions drift from training
   - A/B test model improvements

2. **✅ Feature store**
   - Centralize feature definitions
   - Ensure consistent feature engineering
   - Version control features

## Expected Outcomes After Fixes

- **Prediction range: 5-25%** (more realistic spread)
- **Mean prediction: ~12-15%** (matches training distribution)
- **Risk level distribution:**
  - Low: 60-70%
  - Medium: 20-30%
  - High: 5-15%
- **Model accuracy: 70-85%** (more realistic, less overfit)
- **Feature importance:**
  - Top 5 features: 40-60% total importance
  - No single feature > 30% importance

## Next Steps

1. **Retrain model** with fixes above
2. **Validate predictions** match expected distribution
3. **Update dashboard** to show realistic risk distribution
4. **Monitor** model performance in production

