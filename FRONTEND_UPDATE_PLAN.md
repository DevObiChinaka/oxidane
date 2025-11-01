# Backend API Endpoints Needed

## 1. Pricing Plans API (/api/pricing/)
- GET /api/pricing/plans/ - List all pricing plans (admin)
- POST /api/pricing/plans/ - Create new pricing plan (admin)
- PUT /api/pricing/plans/{id}/ - Update pricing plan (admin)
- DELETE /api/pricing/plans/{id}/ - Delete pricing plan (admin)
- GET /api/pricing/public/ - Public pricing (no auth) - FOR LANDING PAGES

## 2. Coupon Codes API (/api/pricing/coupons/)
- GET /api/pricing/coupons/ - List coupon codes (admin)
- POST /api/pricing/coupons/ - Create coupon code (admin)
- PUT /api/pricing/coupons/{id}/ - Update coupon code (admin)
- DELETE /api/pricing/coupons/{id}/ - Delete coupon code (admin)
- POST /api/pricing/coupons/validate/ - Validate coupon for checkout

## 3. Subscription Enhancement
- Update existing subscription creation to support:
  - Dynamic pricing plans (by plan ID instead of hardcoded types)
  - Coupon code application
  - Plan category and billing cycle tracking

## Implementation Steps:
1. Create serializers for PricingPlan and CouponCode models
2. Create ViewSets with proper permissions
3. Add URL routing
4. Create public pricing endpoint (no authentication)
5. Update subscription creation flow

## Example Response Formats:

### Public Pricing Response:
```json
{
  "plans": [
    {
      "id": "uuid",
      "name": "Monthly Signals", 
      "description": "Premium trading signals",
      "price": 50.00,
      "currency": "USD",
      "plan_category": "signals",
      "billing_cycle": "monthly",
      "is_promotion": true,
      "promotion_text": "Most Popular",
      "telegram_groups": ["signals_monthly"],
      "features": ["20-30 signals/month", "Market analysis", "Support"]
    }
  ],
  "categories": {
    "signals": [...],
    "mentorship": [...], 
    "vip": [...]
  }
}
```

### Coupon Validation Response:
```json
{
  "valid": true,
  "discount_amount": 5.00,
  "final_amount": 45.00,
  "message": "10% discount applied",
  "coupon": {
    "code": "WELCOME10",
    "discount_type": "percentage",
    "discount_value": 10
  }
}
```