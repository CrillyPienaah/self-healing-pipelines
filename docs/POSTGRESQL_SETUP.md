# Alembic Configuration for Database Migrations

## Setup Instructions

### 1. Initialize Alembic

```powershell
# From project root
alembic init alembic
```

### 2. Configure alembic.ini

Edit `alembic.ini` and update:

```ini
# Line ~63
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/self_healing_pipelines
```

### 3. Update alembic/env.py

Replace the imports section with:

```python
from src.db.models import Base
target_metadata = Base.metadata
```

### 4. Create Initial Migration

```powershell
# Create migration
alembic revision --autogenerate -m "Initial schema: pipelines, snapshots, anomalies, fixes, audit_logs"

# Apply migration
alembic upgrade head
```

### 5. Update .env

Add to your `.env` file:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/self_healing_pipelines
```

---

## PostgreSQL Setup (Local Development)

### Option 1: Docker (Recommended)

```powershell
# Create docker-compose.yml
docker-compose up -d
```

### Option 2: Local Installation

1. Download PostgreSQL: https://www.postgresql.org/download/windows/
2. Install with password: `postgres`
3. Create database:

```sql
CREATE DATABASE self_healing_pipelines;
```

---

## Migration Commands

```powershell
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```
