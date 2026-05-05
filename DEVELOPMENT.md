# Development Guide

## Setting Up Development Environment

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15
- Redis 7
- Optional: Docker & Docker Compose

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Create directories for logs
mkdir -p logs

# Initialize database (ensure PostgreSQL is running)
python -c "from app.core.database import init_db; init_db()"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## API Development

### Adding a New Endpoint

1. **Create the route file** in `app/api/`:

```python
# app/api/my_endpoint.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/my-endpoint", tags=["my-feature"])

@router.get("/", response_model=MySchema)
async def get_my_data(db: Session = Depends(get_db)):
    """Get my data."""
    # Implementation here
    pass
```

2. **Include in main app** in `app/main.py`:

```python
from app.api.my_endpoint import router as my_endpoint_router
app.include_router(my_endpoint_router)
```

### Database Model Development

1. **Define model** in `app/models/db.py`:

```python
from app.core.database import Base

class MyModel(Base):
    __tablename__ = "my_models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    # ... other fields
```

2. **Create Pydantic schema** in `app/models/schemas.py`:

```python
class MyModelResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True
```

3. **Run migrations** (if using Alembic):

```bash
alembic revision --autogenerate -m "Add MyModel"
alembic upgrade head
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_api.py::test_health_check
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test test_name
```

### Manual API Testing

Use the provided test script:

```bash
chmod +x scripts/test_api.sh
./scripts/test_api.sh
```

Or use curl directly:

```bash
# Health check
curl http://localhost:8000/health

# Create application
curl -X POST http://localhost:8000/decisions/underwrite \
  -H "Content-Type: application/json" \
  -d @sample_application.json
```

## Code Quality

### Formatting

```bash
# Python formatting with Black
pip install black
black backend/app

# Python linting with pylint
pip install pylint
pylint backend/app

# Frontend formatting
cd frontend
npm install -g prettier
prettier --write src/
```

### Type Checking

```bash
# Python type checking with mypy
pip install mypy
mypy backend/app

# TypeScript checking (automatic in React)
cd frontend
npm run build
```

## Debugging

### Backend Debugging

```python
# Add breakpoint in code
import pdb
pdb.set_trace()

# Or use IDE debugger (VSCode, PyCharm)
# Set breakpoint and run:
python -m pdb app/main.py
```

### Frontend Debugging

```javascript
// Use browser DevTools (F12)
// Add console.log for debugging
console.log('Debug info:', variable);

// Use debugger statement
debugger;
```

### Database Inspection

```bash
# Connect to PostgreSQL
psql postgresql://user:pass@localhost:5432/underwriting_db

# Useful commands
\dt                    # List tables
SELECT * FROM decisions LIMIT 10;  # View data
\d decisions           # Show table schema
```

### Redis Inspection

```bash
# Connect to Redis
redis-cli

# Useful commands
KEYS *                 # List all keys
GET key_name           # Get value
DEL key_name           # Delete key
FLUSHDB                # Clear database
```

## Logging

### Configure Logging

Edit `app/config.py`:

```python
LOG_LEVEL = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "json"  # json or standard
```

### View Logs

```bash
# Docker logs
docker-compose logs -f api

# Local logs
tail -f logs/app.log

# Search logs
grep "decision_id" logs/app.log
```

## Performance Profiling

### Backend Profiling

```python
# Add to app/main.py
from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

# ... run your code ...

profiler.stop()
print(profiler.output_text(unicode=True))
```

### Frontend Performance

Use React DevTools Profiler:
1. Install React DevTools extension
2. Open DevTools → Profiler
3. Record interactions
4. Analyze component render times

## Common Tasks

### Reset Database

```bash
# Drop all tables and reinitialize
python -c "
from app.core.database import Base, engine, init_db
Base.metadata.drop_all(bind=engine)
init_db()
"
```

### Generate Test Data

```bash
# Use test_utils for sample data
from scripts.test_utils import generate_multiple_applications

apps = generate_multiple_applications(100)
```

### Update Dependencies

```bash
# Backend
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt

# Frontend
npm update
npm audit fix
```

### Database Export

```bash
# Backup
pg_dump postgresql://user:pass@localhost/underwriting_db > backup.sql

# Restore
psql postgresql://user:pass@localhost/underwriting_db < backup.sql
```

## Environment Variables

### Development

```env
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://user:pass@localhost:5432/underwriting_db
REDIS_URL=redis://localhost:6379/0
ENABLE_RAG=false  # Disable RAG for faster testing
SIMULATION_MODE=true
```

### Testing

```env
DEBUG=False
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@localhost:5432/underwriting_test_db
REDIS_URL=redis://localhost:6379/15
ENABLE_RAG=false
SIMULATION_MODE=false
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in config
API_PORT=8001
```

### Database Connection Error

```bash
# Verify PostgreSQL is running
psql postgresql://user:pass@localhost:5432/underwriting_db

# Check connection string
echo $DATABASE_URL

# Restart PostgreSQL
docker-compose restart postgres
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install --force-reinstall -r requirements.txt

npm ci  # For frontend (cleaner install)
```

### LLM API Errors

- Check API keys in `.env`
- Verify API keys are valid
- Check rate limits (OpenAI: 3 requests/min for free tier)
- Test with `curl` first:

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## Performance Tips

1. **Use FastAPI's async**: All I/O operations should be async
2. **Cache aggressively**: Features, routing decisions, model metrics
3. **Batch requests**: Group LLM calls when possible
4. **Use appropriate models**: Don't use GPT-4 for simple tasks
5. **Monitor latency**: Track p50, p95, p99 percentiles
6. **Connection pooling**: Configure in `config.py`

## Security Checklist

- [ ] Never commit `.env` files
- [ ] Use environment variables for secrets
- [ ] Validate all inputs
- [ ] Use prepared statements (SQLAlchemy ORM)
- [ ] Implement rate limiting
- [ ] Add HTTPS in production
- [ ] Rotate API keys regularly
- [ ] Log security events
- [ ] Regular security audits

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm test
```

## Documentation

Write docstrings for all functions:

```python
def my_function(param1: str, param2: int) -> str:
    """
    Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When something is invalid
        DatabaseError: When database operation fails
    
    Example:
        >>> result = my_function("test", 42)
        >>> print(result)
    """
    pass
```

## Contributing Guidelines

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -am "Add my feature"`
3. Write tests for new code
4. Run linting and type checks
5. Submit pull request with description
6. Ensure CI passes

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
