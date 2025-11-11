# Coupon Calculation Test Cases

## Exchange Rate: 1 USD = ₦1,437.08

### Test Case 1: SAVE20 (20% off) - Monthly Plan ($30)

**USD Calculations:**
- Base Price: $30.00
- Discount (20%): $6.00
- Final Price: $24.00
- Processing Fee (1.5%): $0.36
- **Total: $24.36**

**NGN Calculations:**
- Base Price: $30.00 × 1,437.08 = ₦43,112.40
- Discount (20%): $6.00 × 1,437.08 = ₦8,622.48
- Final Price: $24.00 × 1,437.08 = ₦34,489.92
- Processing Fee (1.5%): ₦34,489.92 × 0.015 = ₦517.35
- **Total: ₦35,007.27**

### Test Case 2: FLAT5 ($5 off) - Monthly Plan ($30)

**USD Calculations:**
- Base Price: $30.00
- Discount: $5.00
- Final Price: $25.00
- Processing Fee (1.5%): $0.38
- **Total: $25.38**

**NGN Calculations:**
- Base Price: $30.00 × 1,437.08 = ₦43,112.40
- Discount: $5.00 × 1,437.08 = ₦7,185.40
- Final Price: $25.00 × 1,437.08 = ₦35,927.00
- Processing Fee (1.5%): ₦35,927.00 × 0.015 = ₦538.91
- **Total: ₦36,465.91**

### Test Case 3: WELCOME (15% off) - Monthly Plan ($30)

**USD Calculations:**
- Base Price: $30.00
- Discount (15%): $4.50
- Final Price: $25.50
- Processing Fee (1.5%): $0.38
- **Total: $25.88**

**NGN Calculations:**
- Base Price: $30.00 × 1,437.08 = ₦43,112.40
- Discount (15%): $4.50 × 1,437.08 = ₦6,466.86
- Final Price: $25.50 × 1,437.08 = ₦36,645.54
- Processing Fee (1.5%): ₦36,645.54 × 0.015 = ₦549.68
- **Total: ₦37,195.22**

### Test Case 4: SAVE10 (10% off) - Monthly Plan ($30)

**USD Calculations:**
- Base Price: $30.00
- Discount (10%): $3.00
- Final Price: $27.00
- Processing Fee (1.5%): $0.41
- **Total: $27.41**

**NGN Calculations:**
- Base Price: $30.00 × 1,437.08 = ₦43,112.40
- Discount (10%): $3.00 × 1,437.08 = ₦4,311.24
- Final Price: $27.00 × 1,437.08 = ₦38,801.16
- Processing Fee (1.5%): ₦38,801.16 × 0.015 = ₦582.02
- **Total: ₦39,383.18**

## What Changed in the Fix

### Before (Incorrect):
```typescript
const discountAmount = discount?.amount || 0;  // USD amount, not converted!
```
This showed "$6.00" even in NGN mode because it wasn't converting the discount.

### After (Correct):
```typescript
const discountAmountUSD = discount?.amount || 0;
const discountAmount = currency === 'USD' ? discountAmountUSD : convert(discountAmountUSD);
```
Now it shows "₦8,622.48" when in NGN mode.

### Also Added:
- Proper rounding in `formatCurrency()` to avoid floating-point precision issues
- `maximumFractionDigits: 2` to ensure consistent decimal display
- Both discount amount AND final amount are now converted correctly

## Expected UI Display (SAVE20 in NGN):

```
Base Price                           NGN 43,112.40
Exchange Rate       1 USD = 1437.08 NGN
Discount (20%)                      -NGN 8,622.48  ✓ Now correct!
Processing Fee (1.5%)                  NGN 517.35
───────────────────────────────────────────────────
Total Amount                     NGN 35,007.27
                                        Monthly

✓ Coupon applied! You save NGN 8,622.48  ✓ Now correct!
```

### Before (Bug):
The discount showed "NGN 6.00" because it was displaying the USD amount ($6) without conversion.

### After (Fixed):
The discount shows "NGN 8,622.48" which is the correct conversion of $6.00 × 1,437.08 = ₦8,622.48
