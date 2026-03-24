"""
Notification Service
====================
Centralized service for SMS and Email notifications
Supports: Twilio (SMS), SendGrid (Email)
"""

import os
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# TWILIO SMS CONFIGURATION
# ============================================================================

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️ Twilio not installed. Run: pip install twilio")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# ============================================================================
# SENDGRID EMAIL CONFIGURATION
# ============================================================================

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("⚠️ SendGrid not installed. Run: pip install sendgrid")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@medicare-ai.com")


def is_email_configured() -> bool:
    """Return True if SendGrid is installed and the API key is set."""
    # Re-read from env each time so live .env edits are picked up
    load_dotenv(override=True)
    return SENDGRID_AVAILABLE and bool(os.getenv("SENDGRID_API_KEY"))

# ============================================================================
# SMS FUNCTIONS
# ============================================================================

def send_sms(phone: str, message: str) -> bool:
    """
    Send SMS via Twilio
    
    Args:
        phone: Recipient phone number (with country code, e.g., +919876543210)
        message: SMS content (max 160 chars recommended)
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not TWILIO_AVAILABLE:
        print("❌ Twilio not available")
        return False
    
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("❌ Twilio credentials not configured in .env")
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        
        print(f"✅ SMS sent to {phone}: {sms.sid}")
        return True
        
    except Exception as e:
        print(f"❌ SMS failed: {e}")
        return False

# ============================================================================
# EMAIL FUNCTIONS
# ============================================================================

def send_email(to: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Send email via SendGrid.
    Re-reads env vars each call so .env changes take effect without restart.
    """
    load_dotenv(override=True)          # pick up any runtime .env changes
    api_key    = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@medicare-ai.com")

    if not SENDGRID_AVAILABLE:
        print("❌ SendGrid not available. Run: pip install sendgrid")
        return False

    if not api_key:
        print("❌ SENDGRID_API_KEY not set in .env")
        return False
    
    try:
        message = Mail(
            from_email=from_email,
            to_emails=to,
            subject=subject,
            plain_text_content=body,
            html_content=html_body or body
        )
        
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        print(f"✅ Email sent to {to}: Status {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# ============================================================================
# BOOKING NOTIFICATION TEMPLATES
# ============================================================================

def send_booking_confirmation(booking_details: Dict) -> Dict[str, bool]:
    """
    Send booking confirmation via SMS and Email
    
    Args:
        booking_details: {
            'patient_name': str,
            'patient_phone': str,
            'patient_email': str (optional),
            'doctor_name': str,
            'date': str,
            'time': str,
            'booking_id': str
        }
    
    Returns:
        {'sms': bool, 'email': bool}
    """
    results = {'sms': False, 'email': False}
    
    # SMS Message
    sms_message = f"""
MediCare AI - Appointment Confirmed!

Doctor: {booking_details['doctor_name']}
Date: {booking_details['date']}
Time: {booking_details['time']}

Booking ID: {booking_details['booking_id']}

Please arrive 10 minutes early.
    """.strip()
    
    # Email Message
    email_subject = "Appointment Confirmation - MediCare AI"
    email_body = f"""
Dear {booking_details['patient_name']},

Your appointment has been confirmed!

Appointment Details:
- Doctor: {booking_details['doctor_name']}
- Date: {booking_details['date']}
- Time: {booking_details['time']}
- Booking Reference: {booking_details['booking_id']}

Important Instructions:
1. Please arrive 10 minutes before your scheduled time
2. Bring any relevant medical reports
3. Carry a valid ID proof

If you need to reschedule or cancel, please contact us at least 24 hours in advance.

Thank you for choosing MediCare AI!

Best regards,
MediCare AI Team
    """.strip()
    
    # HTML Email (prettier version)
    html_email = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <h2 style="color: #2563eb;">✅ Appointment Confirmed!</h2>
            
            <p>Dear <strong>{booking_details['patient_name']}</strong>,</p>
            
            <p>Your appointment has been successfully confirmed.</p>
            
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1f2937;">📅 Appointment Details</h3>
                <p><strong>Doctor:</strong> {booking_details['doctor_name']}</p>
                <p><strong>Date:</strong> {booking_details['date']}</p>
                <p><strong>Time:</strong> {booking_details['time']}</p>
                <p><strong>Booking ID:</strong> {booking_details['booking_id']}</p>
            </div>
            
            <div style="background-color: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #92400e;">⚠️ Important Instructions</h4>
                <ul>
                    <li>Please arrive 10 minutes before your scheduled time</li>
                    <li>Bring any relevant medical reports</li>
                    <li>Carry a valid ID proof</li>
                </ul>
            </div>
            
            <p style="color: #6b7280; font-size: 14px;">
                If you need to reschedule or cancel, please contact us at least 24 hours in advance.
            </p>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            
            <p style="color: #6b7280; font-size: 12px;">
                Thank you for choosing MediCare AI!<br>
                <strong>MediCare AI Team</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    # Send SMS
    if booking_details.get('patient_phone'):
        results['sms'] = send_sms(booking_details['patient_phone'], sms_message)
    
    # Send Email
    if booking_details.get('patient_email'):
        results['email'] = send_email(
            to=booking_details['patient_email'],
            subject=email_subject,
            body=email_body,
            html_body=html_email
        )
    
    return results

# ============================================================================
# APPOINTMENT REMINDER
# ============================================================================

def send_appointment_reminder(booking_details: Dict) -> Dict[str, bool]:
    """
    Send appointment reminder (24 hours before)
    
    Args:
        booking_details: Same as send_booking_confirmation
    
    Returns:
        {'sms': bool, 'email': bool}
    """
    results = {'sms': False, 'email': False}
    
    # SMS Reminder
    sms_message = f"""
MediCare AI - Appointment Reminder

Your appointment is tomorrow!

Doctor: {booking_details['doctor_name']}
Date: {booking_details['date']}
Time: {booking_details['time']}

See you soon!
    """.strip()
    
    # Email Reminder
    email_subject = "Appointment Reminder - Tomorrow"
    email_body = f"""
Dear {booking_details['patient_name']},

This is a friendly reminder about your appointment tomorrow.

Appointment Details:
- Doctor: {booking_details['doctor_name']}
- Date: {booking_details['date']}
- Time: {booking_details['time']}

Looking forward to seeing you!

Best regards,
MediCare AI Team
    """.strip()
    
    # Send SMS
    if booking_details.get('patient_phone'):
        results['sms'] = send_sms(booking_details['patient_phone'], sms_message)
    
    # Send Email
    if booking_details.get('patient_email'):
        results['email'] = send_email(
            to=booking_details['patient_email'],
            subject=email_subject,
            body=email_body
        )
    
    return results

# ============================================================================
# EMERGENCY ALERT
# ============================================================================

def send_emergency_alert(patient_details: Dict) -> bool:
    """
    Send emergency alert SMS (for critical symptoms)
    
    Args:
        patient_details: {
            'patient_name': str,
            'patient_phone': str,
            'symptoms': str,
            'severity': str
        }
    
    Returns:
        True if sent successfully
    """
    message = f"""
🚨 URGENT - MediCare AI

{patient_details['patient_name']}, your symptoms indicate a potentially serious condition.

Please seek immediate medical attention:
- Visit the nearest Emergency Room
- Call emergency services (108/102)

Do NOT delay. Your health is our priority.
    """.strip()
    
    return send_sms(patient_details['patient_phone'], message)

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_notifications():
    """Test notification service"""
    print("🧪 Testing Notification Service...\n")
    
    # Test SMS
    print("1. Testing SMS...")
    test_sms = send_sms(
        phone="+919876543210",  # Replace with your test number
        message="Test SMS from MediCare AI! 🩺"
    )
    print(f"SMS Test: {'✅ PASS' if test_sms else '❌ FAIL'}\n")
    
    # Test Email
    print("2. Testing Email...")
    test_email = send_email(
        to="test@example.com",  # Replace with your test email
        subject="Test Email from MediCare AI",
        body="This is a test email. If you receive this, the email service is working!"
    )
    print(f"Email Test: {'✅ PASS' if test_email else '❌ FAIL'}\n")
    
    # Test Booking Confirmation
    print("3. Testing Booking Confirmation...")
    test_booking = send_booking_confirmation({
        'patient_name': 'John Doe',
        'patient_phone': '+919876543210',
        'patient_email': 'test@example.com',
        'doctor_name': 'Dr. Smith (Cardiologist)',
        'date': '2026-02-20',
        'time': '10:30 AM',
        'booking_id': 'TEST123'
    })
    print(f"Booking Notification: SMS={'✅' if test_booking['sms'] else '❌'}, Email={'✅' if test_booking['email'] else '❌'}\n")

if __name__ == "__main__":
    test_notifications()
