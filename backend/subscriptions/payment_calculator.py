"""
Payment Calculator - Calculate payment amounts including gateway fees
Implements Option 1: Pass fees to customer (transparent pricing)
"""

from decimal import Decimal
from typing import Dict, Optional


class PaymentCalculator:
    """Calculate payment amounts including Paystack gateway fees"""
    
    # Paystack fee structures (as of 2025)
    FEES = {
        'NGN': {
            'percentage': Decimal('0.015'),  # 1.5%
            'fixed': Decimal('100'),  # ₦100 flat fee
            'cap': Decimal('2000'),  # Maximum ₦2,000 fee
        },
        'USD': {
            'percentage': Decimal('0.039'),  # 3.9%
            'fixed': Decimal('0.50'),  # $0.50 flat fee
            'cap': None,  # No cap for international
        },
        'GHS': {
            'percentage': Decimal('0.029'),  # 2.9%
            'fixed': Decimal('0'),
            'cap': None,
        },
        'ZAR': {
            'percentage': Decimal('0.029'),  # 2.9%
            'fixed': Decimal('0'),
            'cap': None,
        },
    }
    
    # Currency symbols for display
    CURRENCY_SYMBOLS = {
        'NGN': '₦',
        'USD': '$',
        'GHS': 'GH₵',
        'ZAR': 'R',
        'EUR': '€',
        'GBP': '£',
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
            base_amount: The base subscription price (what you want to receive)
            currency: Currency code (NGN, USD, GHS, ZAR)
            pass_fee_to_customer: If True, add fee to customer total. If False, you absorb it.
        
        Returns:
            dict: {
                'base_amount': float,
                'processing_fee': float,
                'total_to_charge': float,
                'you_receive': float,
                'currency': str,
                'currency_symbol': str,
                'fee_passed_to_customer': bool,
                'fee_breakdown': str
            }
        """
        # Get fee structure for currency
        fee_structure = cls.FEES.get(currency, cls.FEES['NGN'])
        
        # Calculate percentage-based fee
        percentage_fee = base_amount * fee_structure['percentage']
        
        # Add fixed fee
        total_fee = percentage_fee + fee_structure['fixed']
        
        # Apply cap if exists
        if fee_structure['cap']:
            total_fee = min(total_fee, fee_structure['cap'])
        
        # Round fee to 2 decimal places
        total_fee = total_fee.quantize(Decimal('0.01'))
        
        if pass_fee_to_customer:
            # Customer pays base + fee (Recommended approach)
            total_to_charge = base_amount + total_fee
            you_receive = base_amount
        else:
            # You absorb the fee
            total_to_charge = base_amount
            you_receive = base_amount - total_fee
        
        # Get currency symbol
        currency_symbol = cls.CURRENCY_SYMBOLS.get(currency, currency)
        
        # Create fee breakdown explanation
        fee_breakdown = cls._create_fee_breakdown(
            fee_structure, 
            base_amount, 
            total_fee,
            currency_symbol
        )
        
        return {
            'base_amount': float(base_amount),
            'processing_fee': float(total_fee),
            'total_to_charge': float(total_to_charge),
            'you_receive': float(you_receive),
            'currency': currency,
            'currency_symbol': currency_symbol,
            'fee_passed_to_customer': pass_fee_to_customer,
            'fee_breakdown': fee_breakdown,
        }
    
    @classmethod
    def _create_fee_breakdown(
        cls,
        fee_structure: Dict,
        base_amount: Decimal,
        total_fee: Decimal,
        currency_symbol: str
    ) -> str:
        """Create human-readable fee breakdown"""
        percentage = fee_structure['percentage'] * 100
        fixed = fee_structure['fixed']
        
        breakdown = f"{percentage}%"
        if fixed > 0:
            breakdown += f" + {currency_symbol}{fixed}"
        
        if fee_structure['cap']:
            breakdown += f" (max {currency_symbol}{fee_structure['cap']})"
        
        return breakdown
    
    @classmethod
    def format_display_message(cls, breakdown: Dict) -> str:
        """
        Format breakdown for display to user
        
        Args:
            breakdown: Result from calculate_total_with_fees()
        
        Returns:
            str: Formatted message for display
        """
        symbol = breakdown['currency_symbol']
        
        message = f"""
**Payment Breakdown**

Subscription Plan: {symbol}{breakdown['base_amount']:,.2f}
Processing Fee ({breakdown['fee_breakdown']}): {symbol}{breakdown['processing_fee']:,.2f}
{'─' * 35}
**Total Amount**: {symbol}{breakdown['total_to_charge']:,.2f}

The processing fee covers payment gateway charges.
You will be charged {symbol}{breakdown['total_to_charge']:,.2f}
        """.strip()
        
        return message
    
    @classmethod
    def calculate_for_paystack(cls, base_amount: Decimal, currency: str = 'NGN') -> Dict:
        """
        Convenience method specifically for Paystack integration
        Always passes fee to customer (recommended)
        
        Returns amount in kobo/cents for Paystack API
        """
        breakdown = cls.calculate_total_with_fees(
            base_amount=base_amount,
            currency=currency,
            pass_fee_to_customer=True
        )
        
        # Paystack requires amount in smallest currency unit (kobo for NGN, cents for USD)
        amount_in_kobo = int(Decimal(str(breakdown['total_to_charge'])) * 100)
        
        return {
            **breakdown,
            'amount_in_kobo': amount_in_kobo,  # For Paystack API
            'paystack_amount': amount_in_kobo,  # Alias
        }


# Example usage and tests
if __name__ == '__main__':
    calculator = PaymentCalculator()
    
    print("=" * 50)
    print("PAYSTACK FEE CALCULATOR - OPTION 1")
    print("Customer pays base + fee (Transparent Pricing)")
    print("=" * 50)
    
    # Test Case 1: NGN 10,000 subscription
    print("\n1. Nigerian Subscription (₦10,000)")
    print("-" * 50)
    breakdown = calculator.calculate_total_with_fees(
        base_amount=Decimal('10000'),
        currency='NGN',
        pass_fee_to_customer=True
    )
    print(f"Base Price: ₦{breakdown['base_amount']:,.2f}")
    print(f"Paystack Fee: ₦{breakdown['processing_fee']:,.2f} ({breakdown['fee_breakdown']})")
    print(f"Customer Pays: ₦{breakdown['total_to_charge']:,.2f}")
    print(f"You Receive: ₦{breakdown['you_receive']:,.2f}")
    
    # Test Case 2: USD 50 subscription
    print("\n2. International Subscription ($50)")
    print("-" * 50)
    breakdown = calculator.calculate_total_with_fees(
        base_amount=Decimal('50'),
        currency='USD',
        pass_fee_to_customer=True
    )
    print(f"Base Price: ${breakdown['base_amount']:,.2f}")
    print(f"Paystack Fee: ${breakdown['processing_fee']:,.2f} ({breakdown['fee_breakdown']})")
    print(f"Customer Pays: ${breakdown['total_to_charge']:,.2f}")
    print(f"You Receive: ${breakdown['you_receive']:,.2f}")
    
    # Test Case 3: Large amount (₦500,000) - hits fee cap
    print("\n3. Large Subscription (₦500,000) - Fee Cap Applied")
    print("-" * 50)
    breakdown = calculator.calculate_total_with_fees(
        base_amount=Decimal('500000'),
        currency='NGN',
        pass_fee_to_customer=True
    )
    print(f"Base Price: ₦{breakdown['base_amount']:,.2f}")
    print(f"Calculated Fee: ₦{(Decimal('500000') * Decimal('0.015') + Decimal('100')):,.2f}")
    print(f"Actual Fee (capped): ₦{breakdown['processing_fee']:,.2f}")
    print(f"Customer Pays: ₦{breakdown['total_to_charge']:,.2f}")
    print(f"You Receive: ₦{breakdown['you_receive']:,.2f}")
    
    # Test Case 4: Paystack-specific calculation
    print("\n4. Paystack API Format (₦10,000)")
    print("-" * 50)
    paystack_data = calculator.calculate_for_paystack(
        base_amount=Decimal('10000'),
        currency='NGN'
    )
    print(f"Customer Pays: ₦{paystack_data['total_to_charge']:,.2f}")
    print(f"Amount for Paystack API: {paystack_data['amount_in_kobo']:,} kobo")
    print(f"(Paystack API requires amount in kobo: Naira × 100)")
    
    # Test Case 5: Display message format
    print("\n5. Customer-Facing Display Message")
    print("-" * 50)
    breakdown = calculator.calculate_total_with_fees(
        base_amount=Decimal('10000'),
        currency='NGN'
    )
    print(calculator.format_display_message(breakdown))
    
    print("\n" + "=" * 50)
    print("✅ All calculations show OPTION 1 approach:")
    print("   Customer sees transparent pricing")
    print("   You receive full subscription amount")
    print("   Everyone understands what they're paying for")
    print("=" * 50)
