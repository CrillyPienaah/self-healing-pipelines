# Self-Healing Data Pipeline Platform - Complete Documentation

**Project Repository:** https://github.com/CrillyPienaah/self-healing-pipelines  
**Author:** Christopher Pienaah  
**Version:** 0.2.0  
**Last Updated:** January 1, 2026  
**Status:** Phase 1 Complete 

---

##  Table of Contents

1. [Project Overview](#project-overview)
2. [Technical Architecture](#technical-architecture)
3. [API Reference](#api-reference)
4. [Development Setup](#development-setup)
5. [Phase 1: Completed Features](#phase-1-completed-features)
6. [Phase 2: Development Roadmap](#phase-2-development-roadmap)
7. [Research Integration](#research-integration)
8. [OpenAI Residency Application](#openai-residency-application)
9. [Quick Commands Reference](#quick-commands-reference)

---

##  Project Overview

### Vision
Build an AI-native platform that autonomously detects and remediates data pipeline failures, eliminating 40% of maintenance toil while providing EU AI Act-compliant audit trails.

### Problem Statement
- **Maintenance Drag:** 64% of data teams spend >50% of time on pipeline maintenance
- **Data Downtime Cost:** \.6M/year per organization
- **Capacity Crisis:** 95% of data teams operate at/above capacity

### Solution
A self-healing platform that:
1. **Monitors** data pipelines for anomalies (schema drift, quality issues)
2. **Detects** problems automatically using ML-based anomaly detection
3. **Generates** fixes using LLM-powered code generation
4. **Remediates** issues with human-in-the-loop approval
5. **Audits** all actions for EU AI Act compliance

### Target Market
- **ICP:** Directors/VPs of Data Engineering at companies with 10-50 data engineers
- **Tech Stack:** Cloud-native (AWS/GCP + Snowflake/BigQuery + dbt)
- **Pain Trigger:** Recent data incident (missed SLA, lost revenue opportunity)
- **TAM:** Database Automation (\.92B  \.70B by 2030) + Data Quality Tools (\.78B  \.34B by 2030)

### Competitive Advantage
- **Regulatory Moat:** EU AI Act compliance built-in (auto-generated audit trails)
- **Technical Differentiation:** Auto-remediation vs. detection-only (Monte Carlo, Datadog)
- **Research Platform:** Generates novel datasets for multi-agent AI research

---

##  Technical Architecture

### Tech Stack

**Backend:**
- FastAPI 0.104.1 (async Python web framework)
- SQLAlchemy 2.0.35+ (ORM - Phase 2)
- Celery + Redis (task queue - Phase 2)

**AI/LLM:**
- OpenAI GPT-4 (fix generation - Phase 2)
- LangChain (agent orchestration - Phase 2)

**Database:**
- In-memory storage (Phase 1 - current)
- SQLite (Phase 2 development)
- PostgreSQL (Phase 3 production)

**Frontend (Phase 3):**
- React + TypeScript
- Recharts (visualization)
- Tailwind CSS

**Deployment (Phase 4):**
- AWS ECS (containers)
- AWS RDS (PostgreSQL)
- AWS Lambda (event-driven remediation)

### System Architecture Diagram

\\\

          Data Pipeline (dbt, Airflow)           

                   Metadata
                  

         Monitoring Agent (FastAPI)              
  - Schema snapshots                             
  - Metrics collection                           

                  
                  

      Anomaly Detection Engine                   
  - Schema drift detection                     
  - Statistical anomaly detection (Phase 2)      
  - Baseline comparison (Phase 2)                

                   Anomaly detected
                  

      LLM-Powered Fix Generator (Phase 2)        
  - Multi-agent system (Detective, Fixer, Critic)
  - Context retrieval (RAG)                      
  - Code generation (SQL, dbt, Python)           

                   Proposed fix
                  

      Human-in-the-Loop Dashboard (Phase 3)      
  - Review proposed fixes                        
  - Approve/reject/edit                          
  - View audit trail                             

                   Approved
                  

      Remediation Engine (Phase 2)               
  - Apply fixes via Git commits                  
  - Execute SQL patches                          
  - Trigger downstream workflows                 

                  
                  

      Audit Trail & Compliance Logger (Phase 2)  
  - EU AI Act model cards                        
  - Change history                               
  - Rollback capabilities                        

\\\

---

##  API Reference

### Base URL
\\\
http://localhost:8000
\\\

### Authentication
Currently: None (open API)  
Phase 2: API key authentication  
Phase 3: OAuth2 + RBAC

---

### Endpoints

#### 1. Root
\\\http
GET /
\\\

**Response:**
\\\json
{
  "message": "Self-Healing Pipeline Platform API",
  "status": "ok",
  "version": "0.1.0"
}
\\\

---

#### 2. Health Check
\\\http
GET /health
\\\

**Response:**
\\\json
{
  "status": "healthy",
  "version": "0.1.0"
}
\\\

---

#### 3. Create Pipeline
\\\http
POST /api/v1/pipelines
\\\

**Request Body:**
\\\json
{
  "name": "orders_pipeline",
  "description": "Daily orders ETL pipeline",
  "source_type": "dbt"
}
\\\

**Response (201 Created):**
\\\json
{
  "id": 1,
  "name": "orders_pipeline",
  "description": "Daily orders ETL pipeline",
  "source_type": "dbt",
  "created_at": "2026-01-01T10:00:00.000Z"
}
\\\

**Error (400 Bad Request):**
\\\json
{
  "detail": "Pipeline already exists"
}
\\\

---

#### 4. List Pipelines
\\\http
GET /api/v1/pipelines
\\\

**Response:**
\\\json
{
  "pipelines": [
    {
      "id": 1,
      "name": "orders_pipeline",
      "description": "Daily orders ETL pipeline",
      "source_type": "dbt",
      "created_at": "2026-01-01T10:00:00.000Z"
    },
    {
      "id": 2,
      "name": "customers_pipeline",
      "description": "Customer data sync",
      "source_type": "airflow",
      "created_at": "2026-01-01T11:00:00.000Z"
    }
  ],
  "count": 2
}
\\\

---

#### 5. Record Schema Snapshot
\\\http
POST /api/v1/pipelines/{pipeline_id}/snapshots
\\\

**Path Parameters:**
- \pipeline_id\ (integer, required): Pipeline ID

**Request Body:**
\\\json
{
  "columns": [
    {"name": "order_id", "type": "integer"},
    {"name": "customer_id", "type": "integer"},
    {"name": "total", "type": "decimal"}
  ],
  "row_count": 1000
}
\\\

**Response (No Drift):**
\\\json
{
  "snapshot_id": 1,
  "schema_hash": "a3f2c1d5e7b9...",
  "drift_detected": false,
  "snapshot_time": "2026-01-01T10:05:00.000Z"
}
\\\

**Response (Drift Detected):**
\\\json
{
  "snapshot_id": 2,
  "schema_hash": "b4e3d2f6c8a0...",
  "drift_detected": true,
  "snapshot_time": "2026-01-01T10:10:00.000Z"
}
\\\

**Error (404 Not Found):**
\\\json
{
  "detail": "Pipeline not found"
}
\\\

---

#### 6. Get Anomalies
\\\http
GET /api/v1/pipelines/{pipeline_id}/anomalies
\\\

**Path Parameters:**
- \pipeline_id\ (integer, required): Pipeline ID

**Query Parameters:**
- \unresolved_only\ (boolean, optional, default: true): Filter for unresolved anomalies only

**Response:**
\\\json
{
  "anomalies": [
    {
      "id": 1,
      "pipeline_id": 1,
      "type": "schema_drift",
      "severity": "medium",
      "description": "Schema changed from 3 to 4 columns",
      "detected_at": "2026-01-01T10:10:00.000Z",
      "resolved": null,
      "details": {
        "old_columns": [
          {"name": "order_id", "type": "integer"},
          {"name": "customer_id", "type": "integer"},
          {"name": "total", "type": "decimal"}
        ],
        "new_columns": [
          {"name": "order_id", "type": "integer"},
          {"name": "customer_id", "type": "integer"},
          {"name": "total", "type": "decimal"},
          {"name": "order_date", "type": "date"}
        ]
      }
    }
  ],
  "count": 1
}
\\\

---

#### 7. Get Snapshot History
\\\http
GET /api/v1/pipelines/{pipeline_id}/snapshots
\\\

**Path Parameters:**
- \pipeline_id\ (integer, required): Pipeline ID

**Query Parameters:**
- \limit\ (integer, optional, default: 10): Number of recent snapshots to return

**Response:**
\\\json
{
  "snapshots": [
    {
      "id": 2,
      "pipeline_id": 1,
      "schema_hash": "b4e3d2f6c8a0...",
      "columns": [
        {"name": "order_id", "type": "integer"},
        {"name": "customer_id", "type": "integer"},
        {"name": "total", "type": "decimal"},
        {"name": "order_date", "type": "date"}
      ],
      "row_count": 1050,
      "snapshot_time": "2026-01-01T10:10:00.000Z"
    },
    {
      "id": 1,
      "pipeline_id": 1,
      "schema_hash": "a3f2c1d5e7b9...",
      "columns": [
        {"name": "order_id", "type": "integer"},
        {"name": "customer_id", "type": "integer"},
        {"name": "total", "type": "decimal"}
      ],
      "row_count": 1000,
      "snapshot_time": "2026-01-01T10:05:00.000Z"
    }
  ],
  "count": 2
}
\\\

---

##  Development Setup

### Prerequisites
- Python 3.11+ (tested on 3.14.2)
- Git
- VS Code (recommended)

### Installation

\\\powershell
# Clone repository
git clone https://github.com/CrillyPienaah/self-healing-pipelines.git
cd self-healing-pipelines

# Create virtual environment
py -m venv .venv
.\.venv\Scripts\Activate

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
\\\

### Run Development Server

\\\powershell
# Start API server with auto-reload
python -m uvicorn src.api.main:app --reload

# Server will be available at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
\\\

### Run Tests

\\\powershell
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Open coverage report
start htmlcov/index.html
\\\

### Code Quality

\\\powershell
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/

# Lint with flake8
flake8 src/ tests/

# Run all pre-commit hooks
pre-commit run --all-files
\\\

### VS Code Tasks

Press \Ctrl+Shift+B\ to run FastAPI server  
Press \Ctrl+Shift+P\  "Tasks: Run Test Task" to run tests

---

##  Phase 1: Completed Features

### Week 1-3 Deliverables

** Development Environment**
- FastAPI backend configured
- VS Code with debugging, tasks, and launch configs
- Pre-commit hooks for code quality (black, flake8, isort)
- Testing framework (pytest, pytest-cov, pytest-asyncio)
- Git repository with proper .gitignore

** Pipeline Management**
- Register pipelines for monitoring
- List all registered pipelines
- Pipeline metadata storage (name, description, source_type)
- Unique pipeline names enforced

** Schema Drift Detection**
- Record schema snapshots with column metadata
- Calculate SHA-256 hash for schema comparison
- Automatic drift detection on new snapshots
- Anomaly creation when drift detected
- Track old vs. new column sets

** API Documentation**
- Swagger UI (FastAPI automatic docs at /docs)
- ReDoc alternative documentation (/redoc)
- All endpoints fully documented
- Example requests and responses
- Interactive API testing

### Current Metrics
- **Test Coverage:** 100% (3/3 tests passing)
- **API Endpoints:** 7 operational
- **Lines of Code:** ~250 Python
- **Anomaly Types Supported:** 1 (schema_drift)
- **Performance:** <50ms average response time

### Demo Walkthrough

1. **Create Pipeline:**
   \\\ash
   curl -X POST http://localhost:8000/api/v1/pipelines \
     -H "Content-Type: application/json" \
     -d '{"name": "orders_pipeline", "description": "Daily orders ETL"}'
   \\\

2. **Record Initial Snapshot:**
   \\\ash
   curl -X POST http://localhost:8000/api/v1/pipelines/1/snapshots \
     -H "Content-Type: application/json" \
     -d '{"columns": [{"name": "order_id", "type": "int"}, {"name": "total", "type": "decimal"}], "row_count": 1000}'
   \\\

3. **Simulate Schema Drift:**
   \\\ash
   curl -X POST http://localhost:8000/api/v1/pipelines/1/snapshots \
     -H "Content-Type: application/json" \
     -d '{"columns": [{"name": "order_id", "type": "int"}, {"name": "total", "type": "decimal"}, {"name": "currency", "type": "varchar"}], "row_count": 1050}'
   \\\

4. **Check for Anomalies:**
   \\\ash
   curl http://localhost:8000/api/v1/pipelines/1/anomalies
   \\\

---

##  Phase 2: Development Roadmap (Months 4-6)

### Week 4-6: LLM Fix Generation

**Goal:** Integrate OpenAI API to generate SQL/dbt fixes for detected anomalies

**Tasks:**

1. **Install Dependencies**
   \\\powershell
   pip install openai langchain langchain-openai
   \\\

2. **Create Fix Generator Agent**
   \\\python
   # src/agents/fix_generator.py
   from langchain.chat_models import ChatOpenAI
   from langchain.prompts import ChatPromptTemplate
   
   class FixGenerator:
       def __init__(self, api_key: str):
           self.llm = ChatOpenAI(
               model="gpt-4",
               temperature=0.2,
               api_key=api_key
           )
       
       def generate_fix(self, anomaly: dict) -> dict:
           prompt = ChatPromptTemplate.from_template("""
           You are a data engineering expert. Given this schema drift:
           
           Old columns: {old_columns}
           New columns: {new_columns}
           Pipeline: {pipeline_name}
           Source: {source_type}
           
           Generate a fix in the following format:
           1. Diagnosis: What caused this drift?
           2. Fix Code: SQL or dbt code to handle the change
           3. Rollback Plan: How to undo if needed
           4. Confidence: 0-100 score
           
           Be specific and production-ready.
           """)
           # ... implementation
   \\\

3. **Add Endpoints**
   - \POST /api/v1/anomalies/{anomaly_id}/propose-fix\
   - \GET /api/v1/fixes/{fix_id}\
   - \POST /api/v1/fixes/{fix_id}/approve\
   - \POST /api/v1/fixes/{fix_id}/reject\

**Deliverables:**
- LLM-powered fix generator operational
- Multi-agent system (Detective  Fixer  Critic agents)
- Fix storage with confidence scores
- Human approval workflow API

**Success Criteria:**
- 80%+ fix accuracy (measured on test cases)
- <30 second generation time
- Human approval rate >60%

---

### Week 7-9: Additional Anomaly Detection

**Goal:** Detect more types of pipeline issues beyond schema drift

**New Anomaly Types:**

1. **Null Value Spike**
   \\\python
   def detect_null_spike(current_snapshot, baseline):
       for col in current_snapshot['columns']:
           current_null_rate = col['null_count'] / current_snapshot['row_count']
           baseline_null_rate = get_baseline_null_rate(col['name'])
           
           if current_null_rate > baseline_null_rate * 2:  # 2x threshold
               create_anomaly('null_spike', severity='high')
   \\\

2. **Row Count Anomaly**
   \\\python
   def detect_row_count_anomaly(current, baseline):
       percent_change = abs(current - baseline) / baseline
       
       if percent_change > 0.20:  # >20% deviation
           severity = 'critical' if percent_change > 0.50 else 'high'
           create_anomaly('row_count_anomaly', severity=severity)
   \\\

3. **Data Type Mismatch**
   - Detect when column types change unexpectedly
   - Flag potential data corruption
   - Suggest CAST fixes

4. **Column Rename Detection**
   - Use Levenshtein distance for fuzzy matching
   - Detect likely renames (e.g., "order_id"  "orderid")
   - Suggest alias/view fixes
   - Prevent false schema drift alerts

**Deliverables:**
- 4 new anomaly detection algorithms
- Statistical baseline models (rolling average, std dev)
- Configurable thresholds per pipeline
- Anomaly severity classification logic

---

### Week 10-12: React Dashboard

**Goal:** Build user interface for fix approval and pipeline monitoring

**Features:**

1. **Pipeline Dashboard**
   - List all pipelines with health status
   - Visual indicators (healthy/warning/critical)
   - Quick stats (total anomalies, uptime %)

2. **Anomaly Timeline**
   - Chronological view of all anomalies
   - Filter by type, severity, status
   - Search by pipeline or description

3. **Fix Approval Interface**
   - Side-by-side diff view (old vs. new)
   - Syntax-highlighted code preview
   - Approve/Reject/Edit buttons
   - Comment/feedback field

4. **Audit Trail Viewer**
   - Complete history of all actions
   - Who approved/rejected fixes
   - Execution logs
   - Rollback history

**Tech Stack:**
\\\json
{
  "framework": "React 18 + TypeScript",
  "styling": "Tailwind CSS",
  "charts": "Recharts",
  "state": "React Query + Zustand",
  "routing": "React Router v6"
}
\\\

**API Integration:**
\\\	ypescript
// src/api/client.ts
export const fetchPipelines = async () => {
  const response = await fetch('http://localhost:8000/api/v1/pipelines');
  return response.json();
};

export const approveFix = async (fixId: number) => {
  const response = await fetch(\/api/v1/fixes/\/approve\, {
    method: 'POST'
  });
  return response.json();
};
\\\

**Deliverables:**
- React dashboard deployed locally
- 4 main views (dashboard, anomalies, fixes, audit)
- Responsive design (desktop + mobile)
- Real-time updates via polling

---

##  Research Integration

### Novel Contributions to Multi-Agent AI Research

This platform generates three unique research artifacts:

---

#### 1. Dataset: (Failure, Context, Fix) Triples

**What:**
A dataset of 1,000+ examples of:
- Pipeline failure (schema drift, data quality issue)
- Contextual metadata (upstream changes, lineage, business impact)
- Successful remediation (code fix, outcome, downtime)

**Example:**
\\\json
{
  "failure": {
    "type": "schema_drift",
    "pipeline": "orders_etl",
    "old_schema": ["order_id", "total", "customer_id"],
    "new_schema": ["order_id", "total", "customer_id", "currency"]
  },
  "context": {
    "upstream_change": "Stripe API v2  v3 migration",
    "change_date": "2026-01-15T10:30:00Z",
    "affected_downstream": ["sales_dashboard", "finance_report"],
    "business_impact": "Revenue reporting blocked for 2 hours"
  },
  "fix": {
    "code": "ALTER TABLE orders ADD COLUMN currency VARCHAR(3) DEFAULT 'USD';",
    "language": "SQL",
    "confidence": 95,
    "applied_at": "2026-01-15T10:45:00Z",
    "success": true,
    "downtime_minutes": 0,
    "human_approved": true
  }
}
\\\

**Research Value:**
- First large-scale corpus of causal data pipeline failures
- Enables research on LLM causal reasoning
- Ground truth for program synthesis evaluation

**Research Question:**
*Can LLMs learn to distinguish correlation (schema changed) from causation (upstream API deprecated) in data pipeline failures?*

**Potential Paper:**
"Learning to Debug Data Pipelines via Causal Prompt Engineering"

---

#### 2. Multi-Agent Coordination Under Uncertainty

**Challenge:**
How to orchestrate specialized agents (Detective  Fixer  Critic) without hardcoded, brittle workflows?

**Approach:**
Hierarchical Reinforcement Learning for dynamic agent delegation

**Agent Roles:**
1. **Detective Agent**
   - Performs root cause analysis
   - Uses RAG to retrieve similar past incidents
   - Outputs: Diagnosis, confidence, recommended fixer

2. **Fixer Agent**
   - Generates remediation code
   - Specializations: SQL, dbt, Python, Airflow DAGs
   - Outputs: Fix code, rollback plan, confidence

3. **Critic Agent**
   - Validates fix against data contracts
   - Checks for syntax errors, type safety
   - Simulates fix in test environment
   - Outputs: Validation result, risk assessment

**RL Optimization:**
\\\python
# Reward function
reward = (
    fix_success * 100  # Did the fix work?
    - downtime_minutes * 10  # Penalize downtime
    + human_approval * 50  # Bonus for approved fixes
    - false_positives * 20  # Penalize unnecessary interventions
)
\\\

**Research Question:**
*Can RL learn optimal agent delegation policies that outperform rule-based orchestration?*

**Potential Paper:**
"Hierarchical Reinforcement Learning for Dynamic DataOps Workflows"

---

#### 3. Zero-Shot Data Quality Rules via RAG

**Problem:**
Traditional data quality tools require manual rule creation:
\\\python
# Manual (current state)
expect_column_values_to_be_between('revenue', min=0, max=1000000)
expect_column_values_to_match_regex('email', r'^[a-z]+@[a-z]+\.[a-z]+$')
\\\

But business rules are often in **natural language policy documents**:
> "Revenue must be positive for all transactions. APAC region transactions must use local currency. Email addresses must match the corporate domain (@company.com) for employee records."

**Approach:**
Use RAG + LLMs to infer validation rules from unstructured documentation

\\\python
# Retrieval
policy_docs = retrieve_relevant_policies(column='revenue', region='APAC')

# Generation
rule = llm.generate_validation_rule(
    column='revenue',
    context=policy_docs,
    schema={'type': 'decimal', 'nullable': False}
)

# Output
rule = {
    'check': 'revenue > 0 AND (region != "APAC" OR currency = local_currency)',
    'error_message': 'Revenue must be positive; APAC requires local currency',
    'severity': 'high'
}
\\\

**Research Value:**
- Eliminates manual rule authoring
- Keeps rules in sync with policy changes
- Enables "semantic" data quality checks

**Research Question:**
*Can RAG + fine-tuned LLMs reliably infer domain-specific validation constraints from natural language policies?*

**Potential Paper:**
"Zero-Shot Data Quality Rules via Retrieval-Augmented Business Logic"

---

##  OpenAI Residency Application Strategy

### Core Positioning

**Thesis:**
"I'm building a self-healing data pipeline platform that uses multi-agent systems to autonomously remediate failures. The system generates unique datasets advancing research in causal reasoning, multi-agent coordination, and program synthesiswhile solving a \.6M/year problem affecting millions of companies."

### Why This Matters to OpenAI

1. **Production-Scale Stress Test**
   - Real-world environment for testing LLM reasoning
   - Complex multi-agent coordination
   - Tool use in high-stakes scenarios

2. **Novel Research Datasets**
   - First large-scale (failure, fix, outcome) corpus
   - Causal reasoning ground truth
   - Multi-agent decision trajectories

3. **Massive Real-World Impact**
   - \.6M/year data downtime  millions of companies
   - Enables AI scaling (fixes infrastructure bottleneck)
   - Regulatory relevance (EU AI Act compliance)

### Research Agenda (If Accepted)

**Month 1-3: Dataset Collection & Analysis**
- Deploy beta with 10 pilot customers
- Collect 1,000+ failure examples
- Analyze causal patterns in failures

**Month 4-6: Causal Reasoning Experiments**
- Fine-tune models on causal vs. correlational prompts
- Benchmark against rule-based systems
- Paper draft: "Learning to Debug via Causal Prompts"

**Month 7-9: Multi-Agent RL**
- Train RL agent for dynamic workflow optimization
- Compare against hardcoded orchestration
- Paper draft: "Hierarchical RL for DataOps"

**Month 10-12: Zero-Shot Quality Rules**
- Build RAG pipeline for policy  rule generation
- Evaluate on 100+ real company policies
- Paper draft: "Zero-Shot Data Quality via RAG"

### Timeline to Application

- **Month 0-3:** MVP with schema drift detection  (DONE)
- **Month 4-6:** LLM fix generation + multi-agent system
- **Month 7-9:** Beta with 3-10 pilot customers
- **Month 9:** Collect preliminary results for application
- **Month 10:** Submit OpenAI Residency 2026 application

### Supporting Materials for Application

1. **GitHub Repository:** https://github.com/CrillyPienaah/self-healing-pipelines
2. **Demo Video:** 2-min Loom showing schema drift  fix generation  approval
3. **Preliminary Results:** Failure dataset (500+ examples), fix accuracy metrics
4. **Research Proposal:** 3 papers (causal reasoning, multi-agent RL, zero-shot quality)

---

##  Quick Commands Reference

### Development

\\\powershell
# Activate virtual environment
.\.venv\Scripts\Activate

# Start API server with auto-reload
python -m uvicorn src.api.main:app --reload

# Start API server on different port
python -m uvicorn src.api.main:app --reload --port 8001

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/

# Type check (when mypy is added)
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
\\\

### Git Workflow

\\\powershell
# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "feat: add LLM fix generation"

# Push to GitHub
git push origin main

# Create tag for milestone
git tag -a v0.3.0 -m "Phase 2 complete: LLM fix generation"
git push origin v0.3.0

# View commit history
git log --oneline --graph

# Create new branch
git checkout -b feature/react-dashboard
\\\

### Deployment (Phase 4)

\\\ash
# Build Docker image
docker build -t self-healing-pipelines:latest .

# Run container
docker run -p 8000:8000 self-healing-pipelines:latest

# Docker Compose (with PostgreSQL + Redis)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
\\\

---

##  Success Metrics & KPIs

### Phase 1 (Complete )
-  3/3 tests passing (100% coverage)
-  7 API endpoints operational
-  Schema drift detection working
-  <50ms average API response time
-  Zero downtime in development

### Phase 2 (Target: Month 6)
- [ ] LLM fix generation: 80%+ accuracy
- [ ] Fix generation time: <30 seconds
- [ ] Human approval rate: >60%
- [ ] 4 anomaly types detected
- [ ] Multi-agent system operational
- [ ] 100+ failure examples collected

### Phase 3 (Target: Month 9)
- [ ] 3-10 pilot customers deployed
- [ ] 40% reduction in maintenance time (measured)
- [ ] <15% false positive rate
- [ ] 1,000+ failure examples in dataset
- [ ] React dashboard fully functional
- [ ] <5 second dashboard load time

### Phase 4 (Target: Month 12)
- [ ] 50+ paying customers
- [ ] \ MRR (monthly recurring revenue)
- [ ] SOC 2 Type 1 certified
- [ ] EU AI Act compliant
- [ ] OpenAI Residency application submitted
- [ ] 3 research papers in progress

---

##  Contact & Resources

**Author:** Christopher Pienaah  
**Email:** [Your Email]  
**LinkedIn:** [Your LinkedIn]  
**GitHub:** https://github.com/CrillyPienaah  
**Project Repository:** https://github.com/CrillyPienaah/self-healing-pipelines

**Related Links:**
- API Documentation: http://localhost:8000/docs
- OpenAI Residency: https://openai.com/careers/residency
- EU AI Act: https://artificialintelligenceact.eu
- Northeastern Analytics Program: https://northeastern.edu/analytics

---

##  Changelog

### v0.2.0 (2026-01-01) - Phase 1 Complete
-  FastAPI backend with 7 endpoints
-  Schema drift detection
-  Anomaly tracking
-  Swagger UI documentation
-  Testing framework (100% coverage)

### v0.1.0 (2025-12-30) - Initial Setup
-  Project structure created
-  Development environment configured
-  VS Code tasks and debugging
-  Git repository initialized

---

**Last Updated:** January 1, 2026  
**Version:** 0.2.0  
**Status:** Phase 1 Complete   
**Next Milestone:** LLM Fix Generation (Phase 2, Week 4-6)

---

*This is a living document. Update regularly as the project evolves.*
