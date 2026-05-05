# Architecture Overview

## System Components

### 1. Frontend (React + TypeScript)
- **Dashboard**: System statistics, decision distribution, model performance
- **Application Form**: Full underwriting application with 30+ fields
- **Decision History**: View past decisions with feedback options
- **Analytics**: Detailed metrics on routing, models, and bandit performance
- **Responsive Design**: Mobile-friendly CSS with gradient styling

### 2. Backend (FastAPI + Python)

#### API Layer
- `/health`: Health check endpoints
- `/applications`: Application CRUD operations
- `/decisions`: Underwriting decision endpoint + feedback collection
- `/analytics`: System metrics and performance data

#### Services Layer
- **LLM Service**: Async calls to OpenAI, Gemini, local models
- **ML Service**: Feature extraction, heuristic-based predictions
- **Decision Engine**: Orchestration of all components
- **Feature Store**: Caching computed features
- **RAG Service**: Document retrieval for regulatory context

#### Routing & Optimization
- **LLM Router**: Dynamically selects which model to use
  - Analyzes input complexity
  - Considers confidence thresholds
  - Respects cost/latency budgets
  - Chooses between: ML-only, fast LLM, powerful LLM, or RAG-enhanced

#### Self-Improvement
- **LinUCB Bandit**: Contextual multi-armed bandit
  - Each model is an "arm"
  - Learns which model works best given context
  - Updates on user feedback
  - Converges to optimal model selection

### 3. Data Layer

#### PostgreSQL
- Applications: Full applicant data (30+ fields)
- Decisions: Final decision + reasoning + model used
- DecisionHistory: All decision attempts for audit
- ModelMetrics: Performance tracking per decision
- FeatureStore: Cached features for performance
- BanditArms: Contextual bandit state

#### Redis
- Session caching
- Job queues for async tasks
- Feature cache TTL management

#### FAISS (Vector DB)
- RAG document storage
- Semantic search over policies/regulations

### 4. Infrastructure
- **Docker Compose**: Local development environment
- **PostgreSQL 15**: Primary database
- **Redis 7**: Cache & job queue
- **Uvicorn**: ASGI server for FastAPI
- **Nginx**: Reverse proxy for frontend

## Data Flow

```
User Application (JSON)
         │
         ▼
    FastAPI Gateway
         │
    ┌────┴──────────────┐
    │                   │
    ▼                   ▼
  Store in DB    Feature Extraction
    │                   │
    │            ┌──────▼───────┐
    │            │              │
    │      Risk Scoring    ML Prediction
    │            │              │
    │            └──────┬───────┘
    │                   │
    │            Calculate Complexity
    │                   │
    │            ┌──────▼────────────┐
    │            │  LLM Router       │
    │         Analyzes context      │
    │         Selects model         │
    │         Determines RAG usage  │
    │            └────┬─────────────┘
    │                 │
    │        ┌────────┴────────┐
    │        │                 │
    │    ┌───▼────┐      ┌─────▼──┐
    │    │   LLM  │      │  RAG   │
    │    │ Reason │      │Retrieve│
    │    └───┬────┘      └─────┬──┘
    │        │                 │
    │        └────────┬────────┘
    │                 │
    │         Combine Signals
    │                 │
    │        ┌────────▼────────┐
    │        │ Final Decision  │
    │        │ + Explanation   │
    │        │ + Amount        │
    │        │ + Interest Rate │
    │        └────────┬────────┘
    │                 │
    │      ┌──────────┴──────────┐
    │      │                     │
    │   Return to Client    Store Decision
    │                    + Latency + Cost
    │                    + Model Used
    │
    ▼
User receives decision + explanation
                │
                ▼ (after weeks/months)
            Outcome Known
                │
                ▼
        User Provides Feedback
                │
         ┌──────▼──────┐
         │ Correct?    │
         │             │
         │ Update Bandit│
         │ Learn model  │
         │ preference   │
         └─────────────┘
```

## Cost Optimization Strategy

### Model Selection Decision Tree

```
Application Received
        │
        ├─ Complex? ─ No ──────┐
        │                      │
        │ (DTI > 0.5, Low Credit, etc.)
        │                      │
        │      ┌───────────────┘
        │      │
        │   ML Confidence?
        │      │
        ├─ High (0.85+) ─────────────► SKIP LLM ENTIRELY
        │      │                       (Save Cost)
        │   Low (0.3-0.6)
        │      │
        │      ├─ Cost Budget?
        │      │
        │   Tight ────────────────────► Fast Model
        │      │                        (GPT-3.5 or Local)
        │   Loose
        │      │
        │      └─ Use Best ────────────► Powerful Model
        │         (GPT-4)
        │
        └─ Yes (Complex)
           │
           ├─ High Confidence ─────────► Fast Model + RAG
           │
           └─ Low Confidence ──────────► Powerful Model + RAG
                                        (Full Analysis)
```

## Bandit Learning

### Example Learning Cycle

1. **Initial State**
   - GPT-4: 50 successes / 100 selections (50%)
   - GPT-3.5: 45 successes / 100 selections (45%)
   - Local: 30 successes / 100 selections (30%)

2. **Exploration Phase**
   - Try each model occasionally
   - Track outcomes

3. **Decision**
   - Similar application arrives
   - Bandit suggests: GPT-4 (highest success rate)

4. **Outcome**
   - Decision marked as CORRECT
   - GPT-4 reward increases
   - Next similar app → GPT-4 even more likely

5. **Convergence**
   - After 1000's of decisions
   - Clear winner emerges
   - System optimizes to best model

## Regulatory Compliance

### Fair Lending Safeguards

1. **RAG System**: Access to Fair Lending Act guidelines
2. **Explanation Generation**: Every decision explains reasoning
3. **Audit Trail**: All decisions logged with model used
4. **Bias Monitoring**: Track approval rates by demographics
5. **Appeal Process**: Manual review capability for rejected apps

### Data Protection

- SQL injection prevention (SQLAlchemy ORM)
- Password hashing (bcrypt)
- TLS/SSL ready (configure in production)
- Data encryption at rest (configure in production)

## Performance Characteristics

### Latency Targets
- ML-only: <100ms
- Fast LLM: 1-2s
- Powerful LLM: 2-5s
- RAG + LLM: +500ms

### Cost Targets
- Fast LLM: $0.0005-0.001 per decision
- Powerful LLM: $0.01-0.03 per decision
- Routing saves 30-50% on expensive LLM calls

### Throughput
- Single API server: 100-200 decisions/second
- Scales horizontally with more workers
- Database: 10,000+ decisions/day capacity

## Monitoring & Alerting

### Key KPIs
- Decision accuracy (feedback-based)
- Model cost trends
- Latency distribution
- Approval rate anomalies
- Bandit convergence rate

### Metrics Stored
- Per decision: latency, tokens, cost, model, confidence
- Per model: accuracy, cost, latency percentiles
- Per bandit arm: success rate, selections, uncertainty
- System-wide: approval rate, accuracy, total cost

## Future Enhancements

1. **Real ML Models**: Train on historical data
2. **Advanced RAG**: Vector embeddings + reranking
3. **A/B Testing**: Compare routing strategies
4. **Fairness Constraints**: Ensure non-discriminatory decisions
5. **Explainability**: SHAP values for feature importance
6. **Active Learning**: Request human feedback on uncertain cases
7. **Multi-objective Optimization**: Pareto frontier for cost/accuracy
