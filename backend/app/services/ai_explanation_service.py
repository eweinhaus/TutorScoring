"""
AI explanation service using OpenAI GPT-4.
"""
import os
import logging
from typing import Optional, Dict
from decimal import Decimal

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from app.models.student import Student
from app.models.tutor import Tutor
from app.models.match_prediction import MatchPrediction

logger = logging.getLogger(__name__)

# Initialize OpenAI client
_openai_client = None

def _get_openai_client():
    """Get or create OpenAI client."""
    global _openai_client
    
    if _openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY not set - AI explanations will use fallback")
            return None
        
        if OpenAI is None:
            logger.warning("OpenAI library not installed - AI explanations will use fallback")
            return None
        
        _openai_client = OpenAI(api_key=api_key)
    
    return _openai_client


def generate_match_explanation(
    student: Student,
    tutor: Tutor,
    prediction: MatchPrediction,
    mismatch_scores: Optional[Dict] = None
) -> str:
    """
    Generate AI explanation for match quality.
    
    Args:
        student: Student model instance
        tutor: Tutor model instance
        prediction: MatchPrediction model instance
        mismatch_scores: Optional mismatch scores dict
        
    Returns:
        Explanation string (2-3 sentences)
    """
    # Check if explanation already cached
    if prediction.ai_explanation:
        return prediction.ai_explanation
    
    # Try to generate with AI
    client = _get_openai_client()
    if client:
        try:
            explanation = _generate_openai_explanation(
                client, student, tutor, prediction, mismatch_scores
            )
            if explanation:
                return explanation
        except Exception as e:
            logger.error(f"Error generating AI explanation: {e}")
            # Fall through to fallback
    
    # Fallback to rule-based explanation
    return _generate_fallback_explanation(student, tutor, prediction, mismatch_scores)


def _generate_openai_explanation(
    client,
    student: Student,
    tutor: Tutor,
    prediction: MatchPrediction,
    mismatch_scores: Optional[Dict] = None
) -> Optional[str]:
    """Generate explanation using OpenAI GPT-4."""
    try:
        # Build prompt
        prompt = f"""Analyze this tutor-student match and provide a brief 2-3 sentence explanation.

Student Profile:
- Name: {student.name}
- Age: {student.age}
- Preferred Pace: {student.preferred_pace}/5
- Preferred Teaching Style: {student.preferred_teaching_style}
- Communication Style: {student.communication_style_preference}/5

Tutor Profile:
- Name: {tutor.name}
- Age: {tutor.age if tutor.age else 'N/A'}
- Experience: {tutor.experience_years if tutor.experience_years else 'N/A'} years
- Teaching Style: {tutor.teaching_style if tutor.teaching_style else 'N/A'}
- Preferred Pace: {tutor.preferred_pace if tutor.preferred_pace else 'N/A'}/5

Match Quality:
- Compatibility Score: {float(prediction.compatibility_score):.2%}
- Churn Risk: {prediction.risk_level.upper()} ({float(prediction.churn_probability):.2%})
- Pace Mismatch: {float(prediction.pace_mismatch):.2f}
- Style Mismatch: {float(prediction.style_mismatch):.2f}
- Communication Mismatch: {float(prediction.communication_mismatch):.2f}

Provide a 2-3 sentence explanation highlighting:
1. Key compatibility factors
2. Potential strengths of this match
3. Any concerns or mismatches that might affect retention

Focus on specific, actionable insights."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # or "gpt-4o" if available
            messages=[
                {"role": "system", "content": "You are an expert in educational matching and student retention. Provide concise, actionable insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        explanation = response.choices[0].message.content.strip()
        return explanation
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


def _generate_fallback_explanation(
    student: Student,
    tutor: Tutor,
    prediction: MatchPrediction,
    mismatch_scores: Optional[Dict] = None
) -> str:
    """Generate rule-based fallback explanation."""
    risk_level = prediction.risk_level.lower()
    compatibility = float(prediction.compatibility_score)
    
    # Base explanation on risk level and compatibility
    if risk_level == 'low' and compatibility > 0.7:
        return (
            f"This is a strong match with high compatibility ({compatibility:.0%}). "
            f"The student's preferred teaching style ({student.preferred_teaching_style}) aligns well with "
            f"the tutor's style, and their pace preferences are well-matched. "
            f"This match has a low churn risk and should provide a positive learning experience."
        )
    elif risk_level == 'medium':
        return (
            f"This match has moderate compatibility ({compatibility:.0%}) with some potential concerns. "
            f"The pace mismatch ({float(prediction.pace_mismatch):.1f}) and style alignment may require "
            f"attention, but the tutor's experience and communication style could help mitigate risks."
        )
    else:  # high risk
        return (
            f"This match has lower compatibility ({compatibility:.0%}) and higher churn risk. "
            f"Significant mismatches in pace ({float(prediction.pace_mismatch):.1f}), style, or communication "
            f"may lead to student dissatisfaction. Consider alternative matches or proactive "
            f"interventions if this match is selected."
        )


def update_match_prediction_explanation(
    prediction: MatchPrediction,
    explanation: str,
    db
) -> MatchPrediction:
    """
    Update match prediction with AI explanation.
    
    Args:
        prediction: MatchPrediction model instance
        explanation: Explanation string
        db: Database session
        
    Returns:
        Updated MatchPrediction
    """
    prediction.ai_explanation = explanation
    db.commit()
    db.refresh(prediction)
    return prediction

