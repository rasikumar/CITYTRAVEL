from abc import ABC, abstractmethod
from typing import Dict, Any
import uuid
from datetime import datetime

class PaymentProvider(ABC):
    """
    Abstract Payment Provider interface.
    """
    @abstractmethod
    def process_payment(self, amount: float, method: str, passenger_id: int, bus_id: str) -> Dict[str, Any]:
        pass

class MockPaymentProvider(PaymentProvider):
    """
    Simulated Payment Provider for test & MVP environments.
    Transparently simulates Google Pay, PhonePe, Paytm, and RuPay transactions
    without claiming real financial settlement.
    """
    SUPPORTED_PROVIDERS = ["Google Pay", "PhonePe", "Paytm", "RuPay", "gpay", "phonepe", "paytm", "rupay"]

    FARES = {
        "Single": 15.0,
        "Return": 28.0,
        "Day Pass": 50.0,
        "Student": 8.0,
    }

    def process_payment(self, amount: float, method: str, passenger_id: int, bus_id: str) -> Dict[str, Any]:
        tx_id = f"TXN-SIM-{uuid.uuid4().hex[:10].upper()}"
        
        # Standardize provider name
        provider_name = method
        for p in ["Google Pay", "PhonePe", "Paytm", "RuPay"]:
            if p.lower() in method.lower():
                provider_name = p
                break

        return {
            "success": True,
            "transaction_id": tx_id,
            "amount": amount,
            "provider": provider_name,
            "status": "SUCCESS",
            "message": f"Simulated test payment via {provider_name} completed. (No real money transferred)",
            "timestamp": datetime.utcnow().isoformat(),
        }

payment_provider: PaymentProvider = MockPaymentProvider()
