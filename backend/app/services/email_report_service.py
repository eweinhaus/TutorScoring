"""
Email report generation and sending service.
"""
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.models.session import Session as SessionModel
from app.models.tutor import Tutor
from app.models.tutor_score import TutorScore
from app.models.reschedule import Reschedule
from app.services.email_service import get_email_service

logger = logging.getLogger(__name__)
load_dotenv()


def format_insights(tutor_id: str, db: Session) -> str:
    """
    Generate insights text for a tutor.
    
    Args:
        tutor_id: UUID string of the tutor
        db: Database session
        
    Returns:
        Formatted insights string
    """
    tutor_score = db.query(TutorScore).filter(TutorScore.tutor_id == tutor_id).first()
    
    if not tutor_score:
        return "No score data available for this tutor."
    
    insights = []
    
    # Count recent reschedules
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_reschedules = tutor_score.tutor_reschedules_7d or 0
    
    if recent_reschedules > 0:
        insights.append(f"Tutor has rescheduled {recent_reschedules} time(s) in the past 7 days.")
    
    # Risk status
    if tutor_score.is_high_risk:
        insights.append("Tutor is flagged as HIGH RISK due to elevated reschedule rate.")
    else:
        insights.append("Tutor is currently LOW RISK.")
    
    # Rate information
    if tutor_score.reschedule_rate_30d:
        rate = float(tutor_score.reschedule_rate_30d)
        threshold = float(tutor_score.risk_threshold)
        if rate > threshold:
            insights.append(f"Reschedule rate is {rate:.1f}% (above {threshold}% threshold).")
        else:
            insights.append(f"Reschedule rate is {rate:.1f}% (below {threshold}% threshold).")
    
    # Recommendations
    if tutor_score.is_high_risk:
        insights.append("Recommendation: Schedule coaching session to address rescheduling patterns.")
    
    return " ".join(insights)


def generate_session_report(session_id: str, db: Session) -> str:
    """
    Generate HTML email report content for a session.
    
    Args:
        session_id: UUID string of the session
        db: Database session
        
    Returns:
        HTML email content string
    """
    # Fetch session, tutor, and scores
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    tutor = db.query(Tutor).filter(Tutor.id == session.tutor_id).first()
    if not tutor:
        raise ValueError(f"Tutor {session.tutor_id} not found")
    
    tutor_score = db.query(TutorScore).filter(TutorScore.tutor_id == session.tutor_id).first()
    
    # Get insights
    insights = format_insights(str(tutor.id), db)
    
    # Format reschedule rate
    reschedule_rate = "N/A"
    if tutor_score and tutor_score.reschedule_rate_30d:
        reschedule_rate = f"{float(tutor_score.reschedule_rate_30d):.1f}%"
    
    # Format risk status
    risk_status = "LOW RISK"
    risk_color = "#28a745"  # Green
    if tutor_score and tutor_score.is_high_risk:
        risk_status = "HIGH RISK"
        risk_color = "#dc3545"  # Red
    
    # Format session date
    session_date = session.scheduled_time.strftime("%B %d, %Y at %I:%M %p") if session.scheduled_time else "N/A"
    
    # Dashboard URL (placeholder for MVP)
    dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:3000")
    
    # Generate HTML email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Session Report</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h2 style="color: #2c3e50; margin-top: 0;">Session Report</h2>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Session ID:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{session.id}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Date:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{session_date}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Tutor:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{tutor.name}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Student ID:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{session.student_id}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Status:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{session.status.upper()}</td>
            </tr>
        </table>
        
        <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #2c3e50;">Tutor Performance</h3>
            <p><strong>Reschedule Rate (30 days):</strong> {reschedule_rate}</p>
            <p><strong>Risk Status:</strong> <span style="color: {risk_color}; font-weight: bold;">{risk_status}</span></p>
        </div>
        
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <h3 style="margin-top: 0; color: #856404;">Key Insights</h3>
            <p>{insights}</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="{dashboard_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">View Dashboard</a>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #6c757d;">
            <p>This is an automated report from the Tutor Quality Scoring System.</p>
        </div>
    </body>
    </html>
    """
    
    return html_content


def send_session_report(session_id: str, recipient_email: str, db: Session) -> bool:
    """
    Generate and send session report email.
    
    Args:
        session_id: UUID string of the session
        recipient_email: Email address of recipient
        db: Database session
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Generate report content
        html_content = generate_session_report(session_id, db)
        
        # Get email service
        email_service = get_email_service()
        
        # Send email
        subject = f"Session Report - {session_id}"
        success = email_service.send_email(
            to=recipient_email,
            subject=subject,
            html_content=html_content
        )
        
        if success:
            logger.info(f"Session report email sent successfully for session {session_id}")
        else:
            logger.error(f"Failed to send session report email for session {session_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending session report email: {str(e)}")
        return False

