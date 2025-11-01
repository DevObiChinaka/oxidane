"""
Payment calculation utilities for Oxidane platform
Handles payment gateway fee calculations
"""

from decimal import Decimal
from typing import Dict, Optional


class PaymentCalculator:
    """Calculate payment amounts including gateway fees"""
    
    # Paystack fee structures (as of 2025)
    FEES = {
        'NGN': {
            'percentage': Decimal('0.015'),  # 1.5%
            'fixed': Decimal('100'),  # ₦100
            'cap': Decimal('2000'),  # Max ₦2,000 fee
            'description': '1.5% + ₦100 (capped at ₦2,000)'
        },
        'USD': {
            'percentage': Decimal('0.039'),  # 3.9%
            'fixed': Decimal('0.50'),  # $0.50
            'cap': None,  # No cap
            'description': '3.9% + $0.50'
        },
        'GHS': {
            'percentage': Decimal('0.029'),  # 2.9%
            'fixed': Decimal('0'),
            'cap': None,
            'description': '2.9%'
        },
        'ZAR': {
            'percentage': Decimal('0.029'),  # 2.9%
            'fixed': Decimal('0'),
            'cap': None,
            'description': '2.9%'
        },
        'KES': {
            'percentage': Decimal('0.029'),  # 2.9%
            'fixed': Decimal('0'),
            'cap': None,
            'description': '2.9%'
        }
    }
    
    @classmethod
    def calculate_total_with_fees(
        cls, 
        base_amount: Decimal, 
        currency: str = 'NGN', 
        pass_fee_to_customer: bool = True
    ) -> Dict:
        """
        Calculate total amount with payment gateway fees
        
        Args:
            base_amount: The base subscription price
            currency: Currency code (NGN, USD, GHS, ZAR, KES)
            pass_fee_to_customer: If True, add fee to customer total. If False, you absorb it.
        
        Returns:
            dict with payment breakdown
        """
        base_amount = Decimal(str(base_amount))
        fee_structure = cls.FEES.get(currency.upper(), cls.FEES['NGN'])
        
        # Calculate fee
        percentage_fee = base_amount * fee_structure['percentage']
        total_fee = percentage_fee + fee_structure['fixed']
        
        # Apply cap if exists
        if fee_structure['cap']:
            total_fee = min(total_fee, fee_structure['cap'])
        
        # Round to 2 decimal places
        total_fee = total_fee.quantize(Decimal('0.01'))
        
        if pass_fee_to_customer:
            # Customer pays base + fee (you receive full base amount)
            total_to_charge = base_amount + total_fee
            you_receive = base_amount
        else:
            # You absorb the fee (customer pays base, you receive less)
            total_to_charge = base_amount
            you_receive = base_amount - total_fee
        
        return {
            'base_amount': float(base_amount),
            'processing_fee': float(total_fee),
            'total_to_charge': float(total_to_charge),
            'you_receive': float(you_receive),
            'currency': currency.upper(),
            'fee_passed_to_customer': pass_fee_to_customer,
            'fee_description': fee_structure['description']
        }
    
    @classmethod
    def format_breakdown_message(cls, breakdown: Dict) -> str:
        """Format breakdown for display to user"""
        currency_symbols = {
            'NGN': '₦',
            'USD': '$',
            'GHS': 'GH₵',
            'ZAR': 'R',
            'KES': 'KSh'
        }
        
        symbol = currency_symbols.get(breakdown['currency'], breakdown['currency'])
        
        return f"""
Payment Breakdown

Subscription: {symbol}{breakdown['base_amount']:,.2f}
Processing Fee: {symbol}{breakdown['processing_fee']:,.2f}
────────────────────────────
Total: {symbol}{breakdown['total_to_charge']:,.2f}

The processing fee covers payment gateway charges.
        """.strip()
    
    @classmethod
    def get_fee_description(cls, currency: str = 'NGN') -> str:
        """Get fee description for a currency"""
        fee_structure = cls.FEES.get(currency.upper(), cls.FEES['NGN'])
        return fee_structure['description']
    
    @classmethod
    def calculate_reverse_amount(cls, total_received: Decimal, currency: str = 'NGN') -> Dict:
        """
        Calculate base amount from total received (after fees deducted)
        Useful for calculating original price when you know what you want to receive
        
        Args:
            total_received: Amount you want to receive after fees
            currency: Currency code
        
        Returns:
            dict with calculations
        """
        total_received = Decimal(str(total_received))
        fee_structure = cls.FEES.get(currency.upper(), cls.FEES['NGN'])
        
        # Formula: received = charged - (charged * percentage + fixed)
        # Solving for charged: received = charged * (1 - percentage) - fixed
        # charged = (received + fixed) / (1 - percentage)
        
        percentage = fee_structure['percentage']
        fixed = fee_structure['fixed']
        
        amount_to_charge = (total_received + fixed) / (Decimal('1') - percentage)
        
        # Apply cap if exists
        calculated_fee = (amount_to_charge * percentage) + fixed
        if fee_structure['cap']:
            if calculated_fee > fee_structure['cap']:
                # Recalculate with capped fee
                amount_to_charge = total_received + fee_structure['cap']
                calculated_fee = fee_structure['cap']
        
        amount_to_charge = amount_to_charge.quantize(Decimal('0.01'))
        calculated_fee = calculated_fee.quantize(Decimal('0.01'))
        
        return {
            'amount_to_charge': float(amount_to_charge),
            'processing_fee': float(calculated_fee),
            'you_will_receive': float(total_received),
            'currency': currency.upper()
        }


# Example usage
if __name__ == '__main__':
    calculator = PaymentCalculator()
    
    # Example 1: ₦10,000 subscription with fee passed to customer
    print("Example 1: ₦10,000 subscription")
    breakdown = calculator.calculate_total_with_fees(
        base_amount=Decimal('10000'),
        currency='NGN',
        pass_fee_to_customer=True
    )
    print(calculator.format_breakdown_message(breakdown))
    print(f"\nYou receive: ₦{breakdown['you_receive']:,.2f}\n")
    
    # Example 2: What to charge if you want to receive exactly ₦10,000
    print("\nExample 2: Reverse calculation (want to receive ₦10,000)")
    reverse = calculator.calculate_reverse_amount(
        total_received=Decimal('10000'),
        currency='NGN'
    )
    print(f"Charge customer: ₦{reverse['amount_to_charge']:,.2f}")
    print(f"Processing fee: ₦{reverse['processing_fee']:,.2f}")
    print(f"You receive: ₦{reverse['you_will_receive']:,.2f}\n")
    
    # Example 3: USD pricing
    print("\nExample 3: $50 subscription (USD)")
    usd_breakdown = calculator.calculate_total_with_fees(
        base_amount=Decimal('50'),
        currency='USD',
        pass_fee_to_customer=True
    )
    print(calculator.format_breakdown_message(usd_breakdown))
    print(f"You receive: ${usd_breakdown['you_receive']:,.2f}")
