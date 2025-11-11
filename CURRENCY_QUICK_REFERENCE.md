# Currency Conversion - Quick Reference

## 🚀 Quick Start

### Backend API

```bash
# Test the API
curl "http://localhost:8000/api/v1/currency/convert/?from=USD&to=NGN&amount=30"

# Response
{
  "success": true,
  "to_amount": 43112.33,
  "exchange_rate": 1437.0777,
  "cached": true
}
```

### React Hook

```tsx
import { useCurrencyConverter } from '@/hooks/useCurrencyConverter';

function Component() {
  const { convert, loading, error, rate } = useCurrencyConverter({
    fromCurrency: 'USD',
    toCurrency: 'NGN'
  });

  const price = convert(30); // Returns ₦43,112
  
  return (
    <>
      {loading ? 'Loading...' : `₦${price.toFixed(2)}`}
      {error && <span>Showing USD prices</span>}
    </>
  );
}
```

---

## 📋 API Endpoints

| Endpoint | Method | Purpose | Example |
|----------|--------|---------|---------|
| `/api/v1/currency/convert/` | GET | Convert amount | `?from=USD&to=NGN&amount=30` |
| `/api/v1/currency/rates/` | GET | Get all rates | `?base=USD` |

---

## 🎯 Integration Steps

### 1. Update PricingCards Component

```tsx
// frontend/src/components/Pricing/PricingCards.tsx

import { useCurrencyConverter } from '@/hooks/useCurrencyConverter';

// Inside component:
const { convert, loading, error } = useCurrencyConverter({
  fromCurrency: 'USD',
  toCurrency: currency
});

const displayPrice = currency === 'USD' ? plan.base_price : convert(plan.base_price);
```

### 2. Update Pricing Page

```tsx
// frontend/src/app/(pages)/Pricing/page.tsx

// Same as PricingCards
```

### 3. Update Checkout Page

```tsx
// frontend/src/app/(pages)/Checkout/page.tsx

const { convert, rate } = useCurrencyConverter({
  fromCurrency: 'USD',
  toCurrency: selectedCurrency
});

const total = selectedCurrency === 'USD' ? basePrice : convert(basePrice);
```

---

## ✅ Verification

### Backend Test

```bash
cd backend
python test_currency_api.py
# Expected: ✅ 2/2 tests passed
```

### Frontend Test

1. Open `http://localhost:3000/Pricing`
2. Switch currency dropdown to NGN
3. Verify: $30 plan shows ₦43,112 (not ₦48,000)

---

## 🔧 Configuration

### Change Cache Duration

```python
# backend/subscriptions/services/exchange_rate_service.py
CACHE_DURATION_HOURS = 1  # Change to desired hours
```

### Change API Provider

```python
# backend/subscriptions/services/exchange_rate_service.py
EXCHANGERATE_API_URL = "https://new-api.com/latest/{currency}"
```

---

## 📊 Current Rates

| Currency | Old Rate | New Rate | Difference |
|----------|----------|----------|------------|
| NGN | ₦1,600 | ₦1,437.08 | 11% cheaper ✅ |

---

## 📁 Key Files

### Backend
- `backend/subscriptions/api_views.py` (Lines 3674-3873) - API ViewSet
- `backend/subscriptions/services/exchange_rate_service.py` - Rate service
- `backend/subscriptions/urls.py` (Line 55) - URL routing

### Frontend
- `frontend/src/hooks/useCurrencyConverter.ts` - React hook
- `frontend/src/examples/CurrencyConversionExamples.tsx` - Examples

### Documentation
- `CURRENCY_CONVERSION_COMPLETE.md` - Full guide
- `CURRENCY_SESSION_SUMMARY.md` - Implementation summary

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Cached response | 50-100ms |
| Fresh API call | ~600ms |
| Cache duration | 1 hour |
| Supported currencies | 164 |

---

## 🐛 Troubleshooting

### "404 Not Found"
- Check: URL is `/api/v1/currency/convert/` (with trailing slash)
- Fix: Add trailing slash to URL

### "Invalid HTTP_HOST header: testserver"
- Check: Django test client configuration
- Fix: Add `'testserver'` to `settings.ALLOWED_HOSTS`

### Prices not updating
- Check: Currency state is changing
- Check: `autoFetch` is `true` in hook options
- Fix: Use `refresh()` function to manually update

### Network errors
- Check: Backend server is running
- Check: API_URL environment variable is correct
- Fix: Verify `http://localhost:8000/api/v1/currency/convert/` is accessible

---

## 📞 Support

For issues or questions:
1. Check `CURRENCY_CONVERSION_COMPLETE.md` for detailed guide
2. Review examples in `frontend/src/examples/CurrencyConversionExamples.tsx`
3. Run backend tests: `python test_currency_api.py`
4. Check browser console for frontend errors

---

**Status**: ✅ Backend Complete | ✅ React Hook Complete | 🔲 UI Integration Pending
