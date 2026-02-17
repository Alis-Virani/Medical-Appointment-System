"""
Payment Service
===============
Handle payment processing via Razorpay
Supports: Order creation, payment verification, refunds
"""

import os
import hashlib
import hmac
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# RAZORPAY CONFIGURATION
# ============================================================================

try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    print("⚠️ Razorpay not installed. Run: pip install razorpay")

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# Initialize Razorpay client
if RAZORPAY_AVAILABLE and RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None

# ============================================================================
# PAYMENT ORDER CREATION
# ============================================================================

def create_payment_order(
    amount: int,
    currency: str = "INR",
    receipt_id: Optional[str] = None,
    notes: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Create a Razorpay payment order
    
    Args:
        amount: Amount in smallest currency unit (paise for INR)
                Example: For ₹500, pass 50000
        currency: Currency code (default: INR)
        receipt_id: Optional receipt ID for tracking
        notes: Optional metadata dictionary
    
    Returns:
        Order details dict or None if failed
        {
            'id': 'order_xxxxx',
            'amount': 50000,
            'currency': 'INR',
            'receipt': 'receipt_123',
            'status': 'created'
        }
    """
    if not razorpay_client:
        print("❌ Razorpay not configured")
        return None
    
    try:
        if not receipt_id:
            receipt_id = f"rcpt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        order_data = {
            'amount': amount,
            'currency': currency,
            'receipt': receipt_id,
            'payment_capture': 1  # Auto-capture payment
        }
        
        if notes:
            order_data['notes'] = notes
        
        order = razorpay_client.order.create(data=order_data)
        
        print(f"✅ Payment order created: {order['id']}")
        return order
        
    except Exception as e:
        print(f"❌ Order creation failed: {e}")
        return None

# ============================================================================
# PAYMENT VERIFICATION
# ============================================================================

def verify_payment_signature(
    order_id: str,
    payment_id: str,
    signature: str
) -> bool:
    """
    Verify Razorpay payment signature for security
    
    Args:
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID
        signature: Payment signature from Razorpay
    
    Returns:
        True if signature is valid, False otherwise
    """
    if not RAZORPAY_KEY_SECRET:
        print("❌ Razorpay secret not configured")
        return False
    
    try:
        # Generate expected signature
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if is_valid:
            print(f"✅ Payment verified: {payment_id}")
        else:
            print(f"❌ Invalid payment signature")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

# ============================================================================
# PAYMENT STATUS CHECK
# ============================================================================

def get_payment_status(payment_id: str) -> Optional[Dict]:
    """
    Get payment status from Razorpay
    
    Args:
        payment_id: Razorpay payment ID
    
    Returns:
        Payment details dict or None
        {
            'id': 'pay_xxxxx',
            'amount': 50000,
            'currency': 'INR',
            'status': 'captured',
            'method': 'card',
            'email': 'user@example.com',
            'contact': '+919876543210'
        }
    """
    if not razorpay_client:
        print("❌ Razorpay not configured")
        return None
    
    try:
        payment = razorpay_client.payment.fetch(payment_id)
        print(f"✅ Payment status: {payment['status']}")
        return payment
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return None

# ============================================================================
# REFUND PROCESSING
# ============================================================================

def process_refund(
    payment_id: str,
    amount: Optional[int] = None,
    notes: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Process a refund for a payment
    
    Args:
        payment_id: Razorpay payment ID
        amount: Refund amount in paise (None = full refund)
        notes: Optional refund notes
    
    Returns:
        Refund details dict or None
        {
            'id': 'rfnd_xxxxx',
            'payment_id': 'pay_xxxxx',
            'amount': 50000,
            'status': 'processed'
        }
    """
    if not razorpay_client:
        print("❌ Razorpay not configured")
        return None
    
    try:
        refund_data = {}
        
        if amount:
            refund_data['amount'] = amount
        
        if notes:
            refund_data['notes'] = notes
        
        refund = razorpay_client.payment.refund(payment_id, refund_data)
        
        print(f"✅ Refund processed: {refund['id']}")
        return refund
        
    except Exception as e:
        print(f"❌ Refund failed: {e}")
        return None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def rupees_to_paise(rupees: float) -> int:
    """Convert rupees to paise (smallest unit)"""
    return int(rupees * 100)

def paise_to_rupees(paise: int) -> float:
    """Convert paise to rupees"""
    return paise / 100

def format_amount(paise: int, currency: str = "INR") -> str:
    """Format amount for display"""
    rupees = paise_to_rupees(paise)
    if currency == "INR":
        return f"₹{rupees:,.2f}"
    return f"{currency} {rupees:,.2f}"

# ============================================================================
# BOOKING PAYMENT WORKFLOW
# ============================================================================

def create_booking_payment(
    doctor_name: str,
    patient_name: str,
    consultation_fee: float,
    booking_id: str
) -> Optional[Dict]:
    """
    Create payment order for doctor consultation
    
    Args:
        doctor_name: Name of the doctor
        patient_name: Name of the patient
        consultation_fee: Fee in rupees
        booking_id: Booking reference ID
    
    Returns:
        Order details with Razorpay checkout info
    """
    amount_paise = rupees_to_paise(consultation_fee)
    
    notes = {
        'doctor': doctor_name,
        'patient': patient_name,
        'booking_id': booking_id,
        'type': 'consultation_fee'
    }
    
    order = create_payment_order(
        amount=amount_paise,
        currency="INR",
        receipt_id=f"booking_{booking_id}",
        notes=notes
    )
    
    if order:
        # Add display-friendly amount
        order['amount_display'] = format_amount(order['amount'])
        order['razorpay_key_id'] = RAZORPAY_KEY_ID
    
    return order

# ============================================================================
# MOCK PAYMENT (FOR TESTING WITHOUT RAZORPAY)
# ============================================================================

def create_mock_payment_order(amount: int, **kwargs) -> Dict:
    """
    Create a mock payment order for testing
    Use this when Razorpay is not configured
    """
    import random
    import string
    
    order_id = 'order_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
    
    return {
        'id': order_id,
        'amount': amount,
        'currency': kwargs.get('currency', 'INR'),
        'receipt': kwargs.get('receipt_id', 'test_receipt'),
        'status': 'created',
        'amount_display': format_amount(amount),
        'razorpay_key_id': 'test_key_id',
        'mock': True
    }

def verify_mock_payment(order_id: str, payment_id: str, signature: str) -> bool:
    """Mock payment verification (always returns True for testing)"""
    print(f"✅ Mock payment verified: {payment_id}")
    return True

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_payment_service():
    """Test payment service"""
    print("🧪 Testing Payment Service...\n")
    
    # Test 1: Create Order
    print("1. Creating payment order for ₹500...")
    order = create_booking_payment(
        doctor_name="Dr. Sharma (Cardiologist)",
        patient_name="John Doe",
        consultation_fee=500.00,
        booking_id="TEST123"
    )
    
    if order:
        print(f"✅ Order created: {order['id']}")
        print(f"   Amount: {order.get('amount_display', 'N/A')}")
        print(f"   Status: {order['status']}\n")
    else:
        print("❌ Order creation failed\n")
    
    # Test 2: Mock Payment (for testing without Razorpay)
    print("2. Creating mock payment order...")
    mock_order = create_mock_payment_order(
        amount=rupees_to_paise(500),
        receipt_id="mock_receipt_123"
    )
    print(f"✅ Mock order: {mock_order['id']}")
    print(f"   Amount: {mock_order['amount_display']}\n")
    
    # Test 3: Verify Mock Payment
    print("3. Verifying mock payment...")
    is_valid = verify_mock_payment(
        order_id=mock_order['id'],
        payment_id="pay_mock123",
        signature="mock_signature"
    )
    print(f"Verification: {'✅ PASS' if is_valid else '❌ FAIL'}\n")

if __name__ == "__main__":
    test_payment_service()
