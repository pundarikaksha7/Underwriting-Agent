#!/bin/bash
# Example curl commands for testing the API

BASE_URL="http://localhost:8000"

echo "═══════════════════════════════════════════════════════════"
echo "  Underwriting Agent API - Example Requests"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Health check
echo "1. Health Check"
echo "───────────────────────────────────────────────────────────"
curl -s "$BASE_URL/health" | jq .
echo ""
echo ""

# Create and underwrite application
echo "2. Create Application & Get Decision"
echo "───────────────────────────────────────────────────────────"

RESPONSE=$(curl -s -X POST "$BASE_URL/decisions/underwrite" \
  -H "Content-Type: application/json" \
  -d '{
    "application": {
      "full_name": "Jane Smith",
      "email": "jane.smith@example.com",
      "phone": "555-0123",
      "date_of_birth": "1985-06-20",
      "gender": "female",
      "street_address": "456 Oak Avenue",
      "city": "Boston",
      "state": "MA",
      "postal_code": "02101",
      "country": "USA",
      "annual_income": 95000,
      "monthly_expenses": 3200,
      "employment_status": "employed",
      "years_employed": 7,
      "employer": "Financial Services Inc",
      "credit_score": 750,
      "existing_debts": 25000,
      "number_of_accounts": 8,
      "delinquencies": 0,
      "loan_amount": 30000,
      "loan_term_months": 60,
      "loan_purpose": "home",
      "collateral_value": 50000,
      "applicant_notes": "Excellent track record"
    }
  }')

echo "$RESPONSE" | jq .
DECISION_ID=$(echo "$RESPONSE" | jq -r '.decision_id')
echo ""
echo ""

# Get decision details
echo "3. Get Decision Details"
echo "───────────────────────────────────────────────────────────"
curl -s "$BASE_URL/decisions/$DECISION_ID" | jq .
echo ""
echo ""

# Provide feedback
echo "4. Provide Feedback (mark as correct)"
echo "───────────────────────────────────────────────────────────"
curl -s -X POST "$BASE_URL/decisions/$DECISION_ID/feedback" \
  -H "Content-Type: application/json" \
  -d '{"feedback": "correct"}' | jq .
echo ""
echo ""

# Get routing analytics
echo "5. Get Routing Analytics"
echo "───────────────────────────────────────────────────────────"
curl -s "$BASE_URL/analytics/routing" | jq .
echo ""
echo ""

# Get system performance
echo "6. Get System Performance"
echo "───────────────────────────────────────────────────────────"
curl -s "$BASE_URL/analytics/performance" | jq .
echo ""
echo ""

# Get bandit metrics
echo "7. Get Bandit Algorithm Metrics"
echo "───────────────────────────────────────────────────────────"
curl -s "$BASE_URL/analytics/bandit" | jq .
echo ""
echo ""

# Get model comparison
echo "8. Get Model Comparison"
echo "───────────────────────────────────────────────────────────"
curl -s "$BASE_URL/analytics/model-comparison" | jq .
echo ""
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "Test requests completed!"
echo "═══════════════════════════════════════════════════════════"
