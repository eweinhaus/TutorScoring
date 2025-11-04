"""
Email service interface and implementations.
"""
import os
import logging
from typing import Protocol
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class EmailService(Protocol):
    """Protocol for email service implementations."""
    
    def send_email(self, to: str, subject: str, html_content: str) -> bool:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML email content
            
        Returns:
            True if email sent successfully, False otherwise
        """
        ...


class SendGridEmailService:
    """SendGrid email service implementation."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize SendGrid email service.
        
        Args:
            api_key: SendGrid API key (defaults to SENDGRID_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY environment variable is not set")
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            self.SendGridAPIClient = SendGridAPIClient
            self.Mail = Mail
        except ImportError:
            raise ImportError("sendgrid library is not installed. Install with: pip install sendgrid")
    
    def send_email(self, to: str, subject: str, html_content: str) -> bool:
        """
        Send an email via SendGrid.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML email content
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=os.getenv("ADMIN_EMAIL", "noreply@tutorscoring.com"),
                to_emails=to,
                subject=subject,
                html_content=html_content
            )
            
            sg = self.SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            if response.status_code in [200, 202]:
                logger.info(f"Email sent successfully to {to}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {str(e)}")
            return False


def get_email_service() -> EmailService:
    """
    Factory function to get email service instance.
    
    Returns:
        EmailService implementation based on EMAIL_SERVICE env var
        
    Raises:
        ValueError: If EMAIL_SERVICE is not supported
    """
    email_service = os.getenv("EMAIL_SERVICE", "sendgrid").lower()
    
    if email_service == "sendgrid":
        return SendGridEmailService()
    else:
        raise ValueError(f"Unsupported email service: {email_service}")

