"""
Matching algorithm service using Hungarian algorithm for optimal 1-to-1 assignment.
"""
import logging
from typing import List, Dict, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
import numpy as np

try:
    from scipy.optimize import linear_sum_assignment
except ImportError:
    linear_sum_assignment = None

from app.models.student import Student
from app.models.tutor import Tutor
from app.models.match_prediction import MatchPrediction
from app.services.match_prediction_service import get_or_create_match_prediction

logger = logging.getLogger(__name__)


def build_cost_matrix(
    db: Session,
    student_ids: List[UUID],
    tutor_ids: List[UUID]
) -> Tuple[np.ndarray, Dict[Tuple[UUID, UUID], MatchPrediction]]:
    """
    Build cost matrix for Hungarian algorithm.
    
    Cost = churn_probability (we want to minimize total churn risk).
    
    Args:
        db: Database session
        student_ids: List of student UUIDs
        tutor_ids: List of tutor UUIDs
        
    Returns:
        Tuple of:
        - cost_matrix: numpy array of shape (n, n) where cost[i][j] = churn_probability(student[i], tutor[j])
        - predictions_map: Dictionary mapping (student_id, tutor_id) -> MatchPrediction
    """
    n = len(student_ids)
    cost_matrix = np.zeros((n, n))
    predictions_map = {}
    
    # Fetch students and tutors
    students = {s.id: s for s in db.query(Student).filter(Student.id.in_(student_ids)).all()}
    tutors = {t.id: t for t in db.query(Tutor).filter(Tutor.id.in_(tutor_ids)).all()}
    
    # Verify all students and tutors exist
    missing_students = set(student_ids) - set(students.keys())
    missing_tutors = set(tutor_ids) - set(tutors.keys())
    
    if missing_students:
        raise ValueError(f"Students not found: {missing_students}")
    if missing_tutors:
        raise ValueError(f"Tutors not found: {missing_tutors}")
    
    # Build cost matrix and fetch/create predictions
    for i, student_id in enumerate(student_ids):
        student = students[student_id]
        
        for j, tutor_id in enumerate(tutor_ids):
            tutor = tutors[tutor_id]
            
            # Try to fetch existing prediction
            prediction = db.query(MatchPrediction).filter(
                MatchPrediction.student_id == student_id,
                MatchPrediction.tutor_id == tutor_id
            ).first()
            
            # If not found, create it
            if not prediction:
                # Get tutor stats for prediction
                tutor_stats = None
                if tutor.tutor_score:
                    tutor_stats = {
                        'reschedule_rate_30d': float(tutor.tutor_score.reschedule_rate_30d or 0),
                        'total_sessions_30d': tutor.tutor_score.total_sessions_30d,
                        'is_high_risk': tutor.tutor_score.is_high_risk,
                    }
                
                prediction = get_or_create_match_prediction(db, student, tutor, tutor_stats)
            
            # Cost is churn probability (we want to minimize)
            churn_prob = float(prediction.churn_probability)
            cost_matrix[i][j] = churn_prob
            
            # Store prediction for later use
            predictions_map[(student_id, tutor_id)] = prediction
    
    return cost_matrix, predictions_map


def run_optimal_matching(
    db: Session,
    student_ids: List[UUID],
    tutor_ids: List[UUID]
) -> Dict:
    """
    Run Hungarian algorithm to find optimal 1-to-1 matching.
    
    Args:
        db: Database session
        student_ids: List of student UUIDs (must equal tutor_ids length)
        tutor_ids: List of tutor UUIDs (must equal student_ids length)
        
    Returns:
        Dictionary with:
        - matches: List of matched pairs with details
        - total_churn_risk: Sum of churn probabilities
        - avg_churn_risk: Average churn probability
        - total_compatibility: Sum of compatibility scores
        - avg_compatibility: Average compatibility score
        
    Raises:
        ValueError: If lists are not equal length or if scipy is not available
    """
    if len(student_ids) != len(tutor_ids):
        raise ValueError(
            f"Student and tutor lists must be equal length. "
            f"Got {len(student_ids)} students and {len(tutor_ids)} tutors."
        )
    
    if len(student_ids) < 2:
        raise ValueError("At least 2 students and tutors are required for matching.")
    
    if linear_sum_assignment is None:
        raise ImportError(
            "scipy is not installed. Please install it: pip install scipy"
        )
    
    # Build cost matrix
    logger.info(f"Building cost matrix for {len(student_ids)} students and {len(tutor_ids)} tutors")
    cost_matrix, predictions_map = build_cost_matrix(db, student_ids, tutor_ids)
    logger.info(f"Cost matrix shape: {cost_matrix.shape}, min cost: {cost_matrix.min()}, max cost: {cost_matrix.max()}")
    
    # Run Hungarian algorithm
    # Returns (row_indices, col_indices) where row_indices[i] is matched with col_indices[i]
    logger.info("Running Hungarian algorithm...")
    row_indices, col_indices = linear_sum_assignment(cost_matrix)
    logger.info(f"Algorithm completed: {len(row_indices)} matches")
    
    # Build results
    matches = []
    total_churn_risk = 0.0
    total_compatibility = 0.0
    
    for i, j in zip(row_indices, col_indices):
        student_id = student_ids[i]
        tutor_id = tutor_ids[j]
        prediction = predictions_map[(student_id, tutor_id)]
        
        matches.append({
            'student_id': student_id,
            'tutor_id': tutor_id,
            'churn_probability': float(prediction.churn_probability),
            'compatibility_score': float(prediction.compatibility_score),
            'risk_level': prediction.risk_level,
            'pace_mismatch': float(prediction.pace_mismatch),
            'style_mismatch': float(prediction.style_mismatch),
            'communication_mismatch': float(prediction.communication_mismatch),
            'age_difference': prediction.age_difference,
        })
        
        total_churn_risk += float(prediction.churn_probability)
        total_compatibility += float(prediction.compatibility_score)
    
    n = len(matches)
    
    return {
        'matches': matches,
        'total_churn_risk': total_churn_risk,
        'avg_churn_risk': total_churn_risk / n if n > 0 else 0.0,
        'total_compatibility': total_compatibility,
        'avg_compatibility': total_compatibility / n if n > 0 else 0.0,
    }

