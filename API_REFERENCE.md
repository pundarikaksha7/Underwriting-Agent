# Quick API Reference

## Base URL
`http://localhost:8000`

## Health Check
```bash
GET /health
GET /health/ready
```

## Applications

### Create Application
```bash
POST /applications
Content-Type: application/json

{
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "555-1234",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "street_address": "123 Main St",
  "city": "Springfield",
  "state": "IL",
  "postal_code": "62701",
  "country": "USA",
  "annual_income": 75000,
  "monthly_expenses": 2500,
  "employment_status": "employed",
  "years_employed": 5,
  "employer": "Tech Corp",
  "credit_score": 720,
  "existing_debts": 15000,
  "number_of_accounts": 5,
  "delinquencies": 0,
  "loan_amount": 25000,
  "loan_term_months": 60,
  "loan_purpose": "personal",
  "applicant_notes": "Good customer"
}
```

### Get Application
```bash
GET /applications/{application_id}
```

### Update Application
```bash
PUT /applications/{application_id}
```

### List Applications
```bash
GET /applications?skip=0&limit=100&status_filter=approved
```

## Decisions

### Make Underwriting Decision
```bash
POST /decisions/underwrite
Content-Type: application/json

{
  "application": { ...application data... },
  "include_rag": false,
  "force_model": null,  # Optional: "gpt-4", "gpt-3.5-turbo", "gemini-pro", "local-7b"
  "simulate": false
}

Response:
{
  "decision_id": 1,
  "application_id": 1,
  "decision": "approved",  # "approved", "rejected", "conditional", "pending"
  "confidence": 0.85,
  "risk_score": 0.15,
  "approved_amount": 20000,
  "offered_interest_rate": 0.062,
  "reasoning": "...",
  "explanation": "...",
  "model_used": "gpt-3.5-turbo",
  "latency_ms": 1250,
  "total_tokens_used": 450,
  "estimated_cost": 0.0012,
  "rag_used": false,
  "routing_details": {...}
}
```

### Get Decision
```bash
GET /decisions/{decision_id}
```

### Provide Feedback
```bash
POST /decisions/{decision_id}/feedback
Content-Type: application/json

{
  "feedback": "correct",  # "correct" or "incorrect"
  "actual_outcome": {}  # Optional metadata
}
```

## Analytics

### Routing Analytics
```bash
GET /analytics/routing

Response:
{
  "total_decisions": 100,
  "model_distribution": {
    "gpt-4": 15,
    "gpt-3.5-turbo": 60,
    "local-7b": 25
  },
  "avg_latency_by_model": {...},
  "avg_cost_by_model": {...},
  "decision_distribution": {
    "approved": 65,
    "rejected": 25,
    "conditional": 10
  },
  "avg_confidence": 0.76
}
```

### Bandit Metrics
```bash
GET /analytics/bandit

Response:
{
  "gpt-4": {
    "model_name": "gpt-4",
    "num_selections": 15,
    "num_successes": 13,
    "estimated_reward": 0.866,
    "uncertainty": 0.25,
    "avg_cost": 0.015,
    "avg_latency": 3200
  },
  "gpt-3.5-turbo": {...},
  ...
}
```

### System Performance
```bash
GET /analytics/performance

Response:
{
  "total_decisions": 100,
  "approved_count": 65,
  "rejected_count": 25,
  "conditional_count": 10,
  "approval_rate": 65.0,
  "accuracy": 0.92,
  "correct_decisions": 92,
  "incorrect_decisions": 8,
  "avg_latency_ms": 1520,
  "avg_cost_usd": 0.0045,
  "total_cost_usd": 0.45,
  "total_tokens_used": 45000
}
```

### Model Comparison
```bash
GET /analytics/model-comparison

Response:
{
  "gpt-4": {
    "count": 15,
    "approved": 13,
    "approval_rate": 86.7,
    "accuracy": 0.95,
    "avg_latency_ms": 3200,
    "avg_cost_usd": 0.015,
    "avg_confidence": 0.88
  },
  "gpt-3.5-turbo": {...},
  ...
}
```

## Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation error)
- **404**: Not Found
- **500**: Server Error

## Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Authentication

Currently basic JWT scaffold. In production:

```bash
# Include Authorization header
Authorization: Bearer <token>
```

## Rate Limiting

Default: 60 requests per minute per IP (configurable)

Response includes:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1234567890
```

## Pagination

For list endpoints:
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum items to return (default: 100)

## Filtering

For list endpoints, use query parameters:

```bash
GET /applications?status_filter=approved
```

## Field Definitions

### Decision Types
- `approved`: Application approved
- `rejected`: Application rejected
- `conditional`: Approved with conditions
- `pending`: Needs manual review

### Employment Status
- `employed`: Full-time employment
- `self-employed`: Self-employment
- `retired`: Retired
- `unemployed`: Currently unemployed
- `student`: Student

### Loan Purpose
- `personal`: Personal loan
- `home`: Home/mortgage
- `auto`: Auto loan
- `business`: Business loan
- `debt_consolidation`: Consolidation
- `education`: Education loan

### Feedback
- `correct`: Decision was correct (outcome validates it)
- `incorrect`: Decision was incorrect (outcome contradicts it)

## Examples

### Example 1: Simple Auto-Approved Application
```
Input: 
- Credit Score: 800
- DTI: 0.2
- Employment: 10 years stable
- No delinquencies

Flow:
- ML Model: Very confident (0.95)
- Router: Skip LLM (saves cost)
- Decision: APPROVED immediately
- Cost: ~$0

Output: Approved for $25,000 at 3.5%
```

### Example 2: Complex Application Needing Analysis
```
Input:
- Credit Score: 650
- DTI: 0.55
- Recent job change
- Some delinquencies (2)

Flow:
- ML Model: Medium confidence (0.55)
- Router: Use GPT-3.5-turbo (cheap but good)
- LLM: Detailed analysis and reasoning
- Decision: CONDITIONAL (approval with conditions)
- Cost: ~$0.001

Output: Approved for $18,000 at 6.8% with 90-day checkup
```

### Example 3: High-Risk Application
```
Input:
- Credit Score: 580
- DTI: 0.75
- Unemployment, seeking personal loan
- Multiple recent delinquencies

Flow:
- ML Model: Low confidence (0.25)
- Router: Use GPT-4 (best accuracy) + RAG (regulatory context)
- LLM: Comprehensive risk assessment
- RAG: Retrieve Fair Lending guidelines
- Decision: REJECTED with detailed explanation
- Cost: ~$0.03

Output: Application rejected; refer to loan officer for alternative products
```

## Performance Tips

1. **Batch Requests**: Submit multiple applications at once using background jobs
2. **Cache Decisions**: Similar applications can avoid re-processing
3. **Use Force Model**: For testing, force a specific model to avoid routing overhead
4. **Enable RAG Selectively**: Only enable when needed (high complexity cases)
5. **Monitor Metrics**: Check analytics regularly to optimize routing

## Troubleshooting

### Decision Returns "pending"
- LLM service may be down
- API key may be invalid
- Rate limit may be exceeded

**Solution**: Check API logs, verify keys, wait and retry

### Very High Latency
- LLM service is slow
- Database is under load
- Network issues

**Solution**: Check routing strategy, reduce concurrent requests

### Inconsistent Decisions
- Bandit algorithm is exploring
- Feature extraction varies
- LLM temperature is too high

**Solution**: Negative feedback helps bandit converge

### High Cost
- Too many expensive model calls
- Router not optimizing
- RAG is being overused

**Solution**: Adjust router strategy, review routing logs
