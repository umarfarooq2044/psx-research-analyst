"""
PSX Research Analyst - Email Sender
Sends HTML email reports via SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SMTP_SERVER, SMTP_PORT,
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS
)


def send_email(
    subject: str,
    html_content: str,
    recipients: List[str] = None,
    attachments: List[str] = None
) -> bool:
    """
    Send HTML email via SMTP
    
    Args:
        subject: Email subject
        html_content: HTML body content
        recipients: List of recipient emails (uses config if not provided)
        attachments: List of file paths to attach
    
    Returns:
        True if sent successfully, False otherwise
    """
    # Use default recipients if not provided
    if not recipients:
        recipients = [r.strip() for r in EMAIL_RECIPIENTS if r.strip()]
    
    if not recipients:
        print("Error: No recipients configured. Please set EMAIL_RECIPIENTS in .env")
        return False
    
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("Error: Email credentials not configured. Please set EMAIL_SENDER and EMAIL_PASSWORD in .env")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"PSX Research Analyst <{EMAIL_SENDER}>"
        msg['To'] = ", ".join(recipients)
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Attach files if provided
        if attachments:
            for filepath in attachments:
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        filename = os.path.basename(filepath)
                        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                        msg.attach(part)
        
        # Connect and send
        print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            
            print("Logging in...")
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            
            print(f"Sending email to {len(recipients)} recipient(s)...")
            server.sendmail(EMAIL_SENDER, recipients, msg.as_string())
        
        print("[OK] Email sent successfully!")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("Error: SMTP authentication failed. Check your email and app password.")
        print("Note: For Gmail, use an App Password, not your regular password.")
        print("Create one at: Google Account > Security > 2-Step Verification > App Passwords")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_daily_report(html_content: str, save_copy: bool = True) -> bool:
    """
    Send the daily PSX research report
    
    Args:
        html_content: Generated HTML report
        save_copy: If True, save a local copy of the report
    
    Returns:
        True if sent successfully
    """
    # Generate subject with date
    today = datetime.now()
    subject = f"PSX Daily Research Report - {today.strftime('%d %b %Y')}"
    
    # Save local copy if requested
    if save_copy:
        from report.email_template import save_report_to_file
        save_report_to_file(html_content)
    
    # Send email
    return send_email(subject, html_content)


def send_test_email() -> bool:
    """
    Send a test email to verify configuration
    """
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1 style="color: #1a237e;">PSX Research Analyst - Test Email</h1>
        <p>If you're reading this, your email configuration is working correctly!</p>
        <hr>
        <p><strong>Configuration:</strong></p>
        <ul>
            <li>SMTP Server: {}</li>
            <li>SMTP Port: {}</li>
            <li>Sender: {}</li>
        </ul>
        <p style="color: #666; font-size: 12px;">
            Sent at: {}
        </p>
    </body>
    </html>
    """.format(
        SMTP_SERVER,
        SMTP_PORT,
        EMAIL_SENDER,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    return send_email("PSX Research Analyst - Test Email", html)


def validate_email_config() -> dict:
    """
    Validate email configuration and return status
    """
    issues = []
    
    if not EMAIL_SENDER:
        issues.append("EMAIL_SENDER not set in .env")
    elif '@' not in EMAIL_SENDER:
        issues.append("EMAIL_SENDER doesn't look like a valid email")
    
    if not EMAIL_PASSWORD:
        issues.append("EMAIL_PASSWORD not set in .env")
    elif len(EMAIL_PASSWORD) < 8:
        issues.append("EMAIL_PASSWORD seems too short (should be an app password)")
    
    if not EMAIL_RECIPIENTS or not any(r.strip() for r in EMAIL_RECIPIENTS):
        issues.append("EMAIL_RECIPIENTS not set in .env")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'sender': EMAIL_SENDER,
        'recipients_count': len([r for r in EMAIL_RECIPIENTS if r.strip()]) if EMAIL_RECIPIENTS else 0
    }


if __name__ == "__main__":
    # Check configuration
    print("Checking email configuration...\n")
    
    config_status = validate_email_config()
    
    if config_status['valid']:
        print("[OK] Email configuration looks good!")
        print(f"  Sender: {config_status['sender']}")
        print(f"  Recipients: {config_status['recipients_count']}")
        
        # Ask to send test email
        response = input("\nSend test email? (y/n): ")
        if response.lower() == 'y':
            send_test_email()
    else:
        print("[ERROR] Email configuration has issues:")
        for issue in config_status['issues']:
            print(f"  - {issue}")
        print("\nPlease copy .env.example to .env and fill in your credentials.")
