# Model Calibration Fix: Addressing Overconfident Predictions

## Problem Identified

The model was producing **extremely overconfident predictions**:
- **71.2% of predictions** were <1% (overconfident on low churn)
- **9.1% of predictions** were >=90% (overconfident on high churn)
- Many predictions were exactly 0.0% or 99.9% (unrealistic in real-world scenarios)

## Root Cause

1. **XGBoost produces uncalibrated probabilities**: XGBoost is a gradient boosting algorithm optimized for classification accuracy, not probability calibration. It tends to produce overconfident probabilities.

2. **No probability calibration**: The model was trained without any post-processing to calibrate probabilities.

3. **Overfitting to synthetic data**: The model learned the training data patterns too well, leading to extreme confidence.

## Solution: Probability Calibration

Implemented **isotonic regression calibration** using `CalibratedClassifierCV`:

- **Method**: Isotonic regression (piecewise constant, non-decreasing function)
- **Cross-validation**: 3-fold CV to prevent overfitting
- **Result**: More realistic probabilities that better reflect actual uncertainty

### How It Works

1. Train base XGBoost model
2. Use cross-validation to fit calibration mapping
3. Map raw probabilities to calibrated probabilities
4. Preserve model ranking while reducing overconfidence

## Expected Improvements

**Before Calibration:**
- 71.2% predictions <1% (overconfident)
- 9.1% predictions >=90% (overconfident)
- Many exact 0.0% or 99.9% predictions

**After Calibration:**
- More realistic probability distribution
- Fewer extreme predictions
- Better alignment with actual uncertainty
- Probabilities more spread across the range (e.g., 5-15% for low-risk, 60-80% for high-risk)

## Real-World Expectations

In real-world scenarios, churn probabilities should be:
- **Low-risk matches**: 5-20% churn probability (not 0.1%)
- **Medium-risk matches**: 20-60% churn probability
- **High-risk matches**: 60-85% churn probability (not 99.9%)

Calibration ensures probabilities reflect actual uncertainty rather than model overconfidence.

## Next Steps

1. ✅ Re-train model with calibration
2. ✅ Refresh all predictions with calibrated model
3. ⏳ Verify new predictions are more realistic
4. ⏳ Monitor calibration quality over time

