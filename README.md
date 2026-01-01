# Self-Healing Data Pipeline Platform

AI-native platform that autonomously detects and remediates data pipeline failures, eliminating 40% of maintenance toil while providing EU AI Act-compliant audit trails.

## Quick Start

### Prerequisites
- Python 3.11+ (you have 3.14.2 )
- Git

### Setup

1. Create virtual environment:
```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate
```

2. Install dependencies:
```powershell
   pip install -r requirements-dev.txt
```

3. Install pre-commit hooks:
```powershell
   pre-commit install
```

### Development

- **Run API server:** `python -m uvicorn src.api.main:app --reload`
- **Run tests:** `pytest tests/ -v`
- **Format code:** `black src/ tests/`

Or use VS Code:
- **Press Ctrl+Shift+B** to run API server
- **Press Ctrl+Shift+P** → "Tasks: Run Test Task"

### Project Structure
```
src/
├── api/           # FastAPI endpoints
├── agents/        # LLM agents (detective, fixer, critic)
 monitoring/    # Pipeline monitoring logic
 remediation/   # Fix application logic
 dashboard/     # React frontend (later)
```

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Celery
- **AI/LLM:** LangChain, OpenAI
- **Database:** PostgreSQL, Redis
- **Testing:** pytest, pytest-cov

## License

MIT
