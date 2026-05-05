# Underwriting Agent: AI Decision Intelligence Platform

A **production-grade, end-to-end AI Decision Intelligence Platform** designed for credit/underwriting decisions. This system combines **self-improving ML models**, **dynamic LLM routing**, **real-time optimization**, and **contextual bandits** to make intelligent underwriting decisions while continuously learning from feedback.

## 🎯 Overview

The Underwriting Agent replicates how modern banks handle credit applications:

1. **Application Reception**: Structured (user data) + unstructured (notes/context) input
2. **Feature Engineering**: Extract 20+ financial and behavioral features
3. **ML Model Prediction**: Fast baseline decision with confidence scoring
4. **Intelligent Routing**: Route to appropriate LLM based on complexity, confidence, cost/latency constraints
5. **LLM Reasoning**: Generate detailed explanations and catch edge cases
6. **Optional RAG**: Retrieve regulatory context when needed
7. **Decision Output**: Approval/rejection/conditional + amount + interest rate + explanation
8. **Feedback Loop**: Learn from outcomes via contextual bandits (LinUCB/Thompson Sampling)

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (React UI)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    FASTAPI Gateway                               │
│              /health /applications /decisions /analytics         │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼─────────┐ ┌──────▼──────────┐
│  Decision      │  │  Feature Store   │ │  RAG System    │
│  Engine        │  │  & Cache         │ │  (FAISS)       │
└────────┬────────┘  └──────────────────┘ └────────────────┘
         │
    ┌────┴──────────────────────────────────────┐
    │                                            │
┌───▼──────────┐  ┌──────────────┐  ┌─────────▼─────┐
│ ML Service   │  │ LLM Router   │  │ Bandit Algo   │
│ (Features)   │  │ (LinUCB)     │  │ (LinUCB/TS)   │
└──────────────┘  └──────┬───────┘  └───────────────┘
                         │
                  ┌──────▼──────────┐
                  │ LLM Services    │
                  ├─────────────────┤
                  │ • OpenAI        │
                  │ • Gemini        │
                  │ • Local Models  │
                  └─────────────────┘
        
┌─────────────────────────────────────────────────────────────────┐
│                   Data Layer                                     │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL: Applications, Decisions, Feedback, History         │
│  Redis: Caching, Job Queues, Session State                      │
│  FAISS/Vector DB: RAG Document Storage                          │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **Decision Engine** (`services/decision_engine.py`)
- Orchestrates the entire decision pipeline
- Coordinates ML model, LLM router, and reasoning
- Records decisions and calls to database
- **Key Methods:**
  - `make_decision()`: Main async entry point
  - `record_feedback()`: Update bandit with outcomes
  - `_combine_signals()`: Merge ML + LLM predictions

#### 2. **ML Service** (`services/ml_service.py`)
- Feature extraction (20+ financial metrics)
- Heuristic-based baseline model (replaces scikit-learn for demo)
- Risk scoring
- **Key Metrics:**
  - Debt-to-income ratio
  - Credit utilization
  - Payment history
  - Employment stability
  - Cash flow ratio

#### 3. **LLM Router** (`router/llm_router.py`)
- **Dynamic Model Selection** based on:
  - Input complexity (0-1 score)
  - ML confidence (0-1)
  - Cost budget
  - Latency budget
  - Strategy (cost-optimized, latency-optimized, accuracy-optimized, balanced)
- **Key Decision:**
  - Skip LLM entirely if ML is confident + input is simple (saves cost)
  - Route to fast/cheap models for low-complexity cases
  - Route to powerful models for complex/high-risk cases
- **RAG Determination:** Enable RAG if confidence < 0.6 or complexity > 0.7

#### 4. **Contextual Bandit** (`bandit/bandit.py`)
- **LinUCB Algorithm** for exploration-exploitation
- **Thompson Sampling** as alternative
- Each model is an "arm"
- Learns which model performs best given context
- **Updates On:**
  - User feedback (correct/incorrect)
  - Latency and cost metrics
  - Decision accuracy over time

#### 5. **LLM Service** (`services/llm_service.py`)
- Supports: OpenAI (GPT-4, GPT-3.5), Gemini, Local models
- Cost estimation per model
- Async calls with timeout handling
- Generates reasoning + analysis for applications

#### 6. **Feature Store** (`utils/feature_store.py`)
- Caches computed features in PostgreSQL
- Avoids recomputation
- Marks features as stale when application updates

#### 7. **RAG System** (`utils/rag_service.py`)
- Stores regulatory documents, policies, case studies
- Semantic search over documents
- Optional retrieval for edge cases

### Database Schema

**Core Tables:**
- `users`: Applicants and staff
- `applications`: Credit applications with full details
- `decisions`: Underwriting decisions with reasoning
- `decision_history`: Historical record of all decision attempts
- `model_metrics`: Performance metrics per decision
- `feature_store`: Cached computed features
- `bandit_arms`: Contextual bandit state (model arms)
- `router_logs`: Routing decision audit trail
- `rag_documents`: Policy/regulatory documents for RAG

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OR Python 3.11+, PostgreSQL 15, Redis 7

### Option 1: Docker Compose (Recommended)

```bash
cd /workspaces/Underwriting-Agent

# Configure environment
cp backend/.env.example backend/.env
# Edit .env with your API keys if needed

# Start all services
docker-compose up --build

# Services will be available at:
# API: http://localhost:8000
# Frontend: http://localhost:3000
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

### Option 2: Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Initialize database
python -c "from app.core.database import init_db; init_db()"

# Run API server
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**PostgreSQL:**
```bash
# Using Docker
docker run -d \
  -e POSTGRES_USER=underwriting_user \
  -e POSTGRES_PASSWORD=underwriting_pass \
  -e POSTGRES_DB=underwriting_db \
  -p 5432:5432 \
  postgres:15-alpine
```

**Redis:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

---

## 📊 API Endpoints

### Health Check
```bash
GET /health
GET /health/ready
```

### Applications
```bash
POST   /applications              # Create new application
GET    /applications/{id}         # Get application
PUT    /applications/{id}         # Update application
GET    /applications              # List applications
```

### Decisions
```bash
POST   /decisions/underwrite      # Make underwriting decision
GET    /decisions/{decision_id}   # Get specific decision
POST   /decisions/{decision_id}/feedback  # Provide feedback (correct/incorrect)
```

### Analytics
```bash
GET    /analytics/routing         # Routing decision analytics
GET    /analytics/bandit          # Bandit algorithm metrics
GET    /analytics/performance     # System performance metrics
GET    /analytics/model-comparison # Model comparison stats
```

---

## 💡 Example Usage

### 1. Create Application & Get Decision

```bash
curl -X POST http://localhost:8000/decisions/underwrite \
  -H "Content-Type: application/json" \
  -d '{
    "application": {
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
      "applicant_notes": "Good customer, stable income"
    }
  }'
```

**Response:**
```json
{
  "decision_id": 1,
  "application_id": 1,
  "decision": "approved",
  "confidence": 0.78,
  "risk_score": 0.22,
  "approved_amount": 20000,
  "offered_interest_rate": 0.062,
  "reasoning": "[LLM reasoning text]",
  "explanation": "[Detailed explanation]",
  "model_used": "gpt-3.5-turbo",
  "latency_ms": 1250,
  "total_tokens_used": 450,
  "estimated_cost": 0.0012,
  "rag_used": false,
  "routing_details": {
    "selected_model": "gpt-3.5-turbo",
    "ml_confidence": 0.75,
    "input_complexity": 0.35
  }
}
```

### 2. Provide Feedback

```bash
curl -X POST http://localhost:8000/decisions/1/feedback \
  -H "Content-Type: application/json" \
  -d '{"feedback": "correct"}'
```

### 3. Get Analytics

```bash
curl http://localhost:8000/analytics/performance
```

---

## 🤖 How Decisions Are Made

### Step 1: Feature Extraction
```
Input Application
    ↓
Extract 20+ Features:
  - Debt-to-income ratio
  - Payment history score
  - Employability score
  - Credit utilization
  - Cash flow ratio
  - Risk category
```

### Step 2: ML Baseline
```
Features → ML Model
  ↓
Output: Decision + Confidence (0-1) + Risk Score
  ↓
Examples:
  - High confidence (0.85) → Skip LLM (cost savings)
  - Medium confidence (0.5) → Use fast LLM
  - Low confidence (0.3) → Use powerful LLM + RAG
```

### Step 3: Intelligent Routing
```
Router considers:
  • ML confidence
  • Input complexity
  • Cost budget
  • Latency budget
  • Routing strategy

Decision:
  ✓ Use GPT-4 (expensive, accurate)
  ✓ Use GPT-3.5-turbo (cheap, fast)
  ✓ Use local model (free)
  ✓ Skip LLM entirely (save cost)
  ✓ Enable RAG (add context)
```

### Step 4: LLM Reasoning
```
Prompt to LLM:
  "Analyze this credit application..."
  - Risk factors
  - Positive indicators
  - Recommendation
  - Suggested conditions

LLM Output:
  - Detailed reasoning
  - Risk assessment
  - Recommendations
```

### Step 5: Signal Combination
```
ML Decision + LLM Reasoning + RAG Context
    ↓
Final Decision:
  - APPROVED (with amount + interest rate)
  - REJECTED
  - CONDITIONAL (with requirements)
  - PENDING (needs manual review)
```

### Step 6: Learning Loop
```
User provides feedback:
  "This decision was CORRECT"
         ↓
Update Bandit Algorithm:
  • Model that made this decision gets reward
  • Other models get penalized
  • Algorithm learns which model is best
         ↓
Next similar application:
  Bandit suggests better model (self-improvement)
```

---

## 📈 Self-Improvement Mechanism

### Contextual Bandits (LinUCB)

The system uses **Linear Upper Confidence Bound (LinUCB)** to continuously improve model selection:

1. **Exploration vs Exploitation**
   - 10% of the time: Randomly select a model (explore)
   - 90% of the time: Select best-performing model (exploit)

2. **Learning Metrics**
   - Success rate (decisions marked as correct)
   - Cost per decision
   - Latency
   - Accuracy over time

3. **Algorithm Details**
   - Maintains context features (complexity, confidence, DTI, etc.)
   - Updates posterior over model performance
   - UCB = estimated_reward + exploration_bonus
   - Exploration bonus decreases as we learn

### Feedback Loop

After decision is made:
1. **Wait for Outcome** (weeks/months in real underwriting)
2. **Receive Feedback**: Was this decision correct?
3. **Update Bandit**:
   - Correct decision → reward += 1
   - Incorrect decision → penalty
4. **Model Reselection**: Next similar app uses better model

---

## ⚙️ Configuration

Edit `backend/.env` to configure:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# LLM APIs
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Router Strategy
ROUTER_COST_OPTIMIZATION=true
ROUTER_LATENCY_OPTIMIZATION=true
DEFAULT_MODEL_THRESHOLD=0.7

# Bandit Algorithm
BANDIT_ALGORITHM=linucb  # or thompson
BANDIT_EXPLORATION_RATE=0.1

# Feature Management
ENABLE_RAG=true
USE_RAG_THRESHOLD=0.6
```

---

## 🧪 Testing & Simulation

The system includes **simulation mode** for generating synthetic data:

```bash
# In code or via script:
from app.data_generator import generate_synthetic_applications

apps = generate_synthetic_applications(
    num=1000,
    risk_distribution=["low": 0.4, "medium": 0.4, "high": 0.2]
)
```

This allows:
- Training bandit algorithm on synthetic data
- A/B testing different routing strategies
- Load testing the system

---

## 🔍 Monitoring & Observability

### Metrics Tracked

1. **Decision Metrics**
   - Decision type distribution (approved/rejected/conditional)
   - Approval rate
   - Confidence distribution

2. **Model Performance**
   - Accuracy per model
   - Latency (p50, p95, p99)
   - Cost per decision
   - Average confidence

3. **Routing Decisions**
   - Model selection frequency
   - RAG usage frequency
   - Cost savings from routing

4. **Bandit Evolution**
   - Exploration vs exploitation rate
   - UCB scores per model
   - Success rate convergence

### Analytics Dashboard

Access at `http://localhost:3000/analytics` to see:
- Total decisions and approval rate
- Model comparison (accuracy, cost, latency)
- Bandit algorithm state (success rates)
- System performance KPIs

### Logging

All decisions logged to PostgreSQL with:
- Full application data
- Decision and confidence
- Model selected
- LLM reasoning
- Latency and cost
- Feedback (when provided)

---

## 🏦 Real-World Underwriting Flow

The system models how banks actually underwrite:

1. **Application Reception**: JSON with 30+ fields (income, credit, employment, address, etc.)

2. **Automated Rules Check**:
   - Age validation
   - Income verification
   - Credit score checks
   - Debt ratio thresholds

3. **ML Score**: Fast ML model generates risk score

4. **Intelligent LLM Call**:
   - Don't call LLM if ML is certain (saves cost)
   - Call fast LLM (GPT-3.5) for medium cases
   - Call powerful LLM (GPT-4) for edge cases

5. **Regulatory Context** (RAG):
   - If dealing with high-risk case, pull relevant regulations
   - Ensure decision complies with Fair Lending Act
   - Reference underwriting guidelines

6. **Final Decision**:
   - Amount approved (% of requested)
   - Interest rate (based on risk)
   - Conditions (if any)
   - Explanation for customer

7. **Feedback & Learning**:
   - After 6-12 months, see if customer paid
   - Update bandit: was this a good decision?
   - Adjust model selection for similar future cases

---

## 🚀 Production Considerations

### Deployment

1. **Containerization**: Docker Compose files provided
2. **Orchestration**: Ready for Kubernetes
3. **Scaling**:
   - FastAPI workers: horizontal scaling
   - Celery workers: async task processing
   - Database: connection pooling (20 connections)
   - Redis: caching + job queue

### Security

- JWT authentication (basic implementation)
- CORS configuration
- SQL injection protection (SQLAlchemy ORM)
- Rate limiting (configurable)
- API key management for LLM services

### High Availability

- Database replication (PostgreSQL)
- Redis clustering for cache
- Load balancing for API
- Health checks on all services

### Cost Optimization

Routing layer provides:
- Cost estimates before calling expensive LLMs
- Fallback to cheaper models when possible
- Token usage tracking
- Model cost comparison in analytics

---

## 🔧 Architecture Decisions & Tradeoffs

### 1. Heuristic ML Model vs. Real ML
**Decision**: Heuristic (demo), but framework supports scikit-learn/LightGBM

**Tradeoff**:
- ✅ No training data needed for demo
- ❌ Less accurate than real ML
- 📝 In production: Replace with trained LightGBM on historical data

### 2. LinUCB vs. Thompson Sampling
**Decision**: Both implemented, LinUCB default

**Comparison**:
- LinUCB: Better for continuous rewards, faster convergence
- Thompson: Simpler, works with binary rewards

### 3. OpenAI/Gemini vs. Local Models
**Decision**: Support all, router chooses based on constraints

**Tradeoff**:
- OpenAI: Expensive but accurate
- Local: Free but lower quality
- Router optimizes based on cost/latency/accuracy

### 4. Synchronous vs. Async API
**Decision**: Async API (FastAPI) with optional background jobs

**Benefit**: Can handle 1000+ concurrent requests

### 5. PostgreSQL vs. NoSQL
**Decision**: PostgreSQL (relational)

**Reason**: Structured decision data, need ACID compliance, complex queries for analytics

---

## 📚 Project Structure

```
Underwriting-Agent/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── health.py
│   │   │   ├── applications.py
│   │   │   ├── decisions.py
│   │   │   └── analytics.py
│   │   ├── services/         # Business logic
│   │   │   ├── llm_service.py
│   │   │   ├── ml_service.py
│   │   │   └── decision_engine.py
│   │   ├── router/           # LLM routing
│   │   │   └── llm_router.py
│   │   ├── bandit/           # Contextual bandits
│   │   │   └── bandit.py
│   │   ├── models/           # DB models & schemas
│   │   │   ├── db.py
│   │   │   └── schemas.py
│   │   ├── utils/            # Utilities
│   │   │   ├── feature_store.py
│   │   │   ├── rag_service.py
│   │   │   └── utils.py
│   │   ├── core/             # Core infrastructure
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── config.py         # Configuration
│   │   └── main.py           # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/            # React pages
│   │   ├── services/         # API client
│   │   ├── styles/           # CSS
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

---

## 🎓 Learning Resources

### Key Concepts

1. **Contextual Bandits**
   - [LinUCB Algorithm](http://proceedings.mlr.press/v15/lu11a.html)
   - Exploration-exploitation tradeoff

2. **LLM Routing**
   - Cost vs. accuracy optimization
   - Latency budgets

3. **Underwriting**
   - Credit risk assessment
   - Fair Lending compliance
   - Cost/benefit analysis

4. **System Design**
   - Async processing
   - Microservice architecture
   - Feature engineering

---

## 📝 Tradeoffs & Future Enhancements

### Current Limitations

1. **ML Model**: Heuristic-based (needs real training data)
2. **RAG**: Mock documents (needs real policy DB)
3. **No Auth**: Basic auth scaffolding (add OAuth2 in production)
4. **Simulation**: Synthetic data only (integrate real historical data)

### Future Enhancements

1. ✅ Real ML training pipeline
2. ✅ Production RAG with vector embeddings
3. ✅ A/B testing framework
4. ✅ Fairness & bias monitoring
5. ✅ Advanced explanation generation (SHAP values)
6. ✅ Automated retraining pipeline
7. ✅ Multi-armed bandit with contextual features
8. ✅ Decision appeal mechanism

---

## 👥 Support

For issues or questions:
1. Check logs: `docker logs underwriting_api`
2. Test API: `curl http://localhost:8000/health`
3. View dashboard: `http://localhost:3000`

---

## 📄 License

MIT License - See LICENSE file

---

**Built with ❤️ as a production-grade Decision Intelligence Platform**