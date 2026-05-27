# 🚇 AI Smart City Commute Planner

A multi-agent AI system for intelligent commute planning using **LangGraph**, **Claude**, **ChromaDB**, **LangSmith**, **MLflow**, and **DeepEval**.

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────┐
│           LangGraph Pipeline                │
│                                             │
│  🔒 PII Guardian ──► 🛡️ Content Filter      │
│         │                                   │
│         ▼                                   │
│  🧭 Intent Parser                           │
│    ┌────┼────┬────────┐                     │
│    ▼    ▼    ▼        ▼                     │
│  Route Traffic Weather Transit  (parallel)  │
│    └────┴────┴────────┘                     │
│         │                                   │
│         ▼                                   │
│  ⭐ Recommendation Agent                    │
│         │                                   │
│         ▼                                   │
│  📊 Evaluator (DeepEval metrics)            │
└─────────────────────────────────────────────┘
    │
    ▼
Streamlit UI
```

## Agents

| Agent | Role |
|-------|------|
| 🔒 PII Guardian | Detects & masks PII (email, phone, SSN, address, CC, passport) |
| 🛡️ Content Filter | Blocks harmful/off-topic queries |
| 🧭 Intent Parser | Extracts origin, destination, preferences |
| 🗺️ Route Planner | Retrieves optimal routes from ChromaDB |
| 🚦 Traffic Analyst | Real-time traffic condition simulation |
| ⛅ Weather Analyst | Weather impact on commute modes |
| 🚌 Transit Advisor | Public transit schedules & connections |
| ⭐ Recommendation | Synthesizes all inputs into final advice |
| 📊 Evaluator | DeepEval-inspired quality scoring |

## Quick Start

### 1. Install dependencies
```bash
cd smart-city-commute-planner
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY at minimum
```

### 3. Launch the UI
```bash
streamlit run ui/app.py
```

### 4. CLI mode
```bash
python run.py "How do I get from Central Station to Tech Park?"
```

## Optional Services

### LangSmith (run tracing)
Set in `.env`:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your key>
```
Enable the toggle in the sidebar.

### MLflow (experiment tracking)
```bash
mlflow ui  # starts at http://localhost:5000
```
Enable the toggle in the sidebar.

### DeepEval (cloud evaluation)
```
DEEPEVAL_API_KEY=<your key>
```
Enable the toggle in the sidebar.

## Tech Stack

- **LangGraph** — Multi-agent workflow orchestration
- **OpenAI GPT-4o** — LLM backbone via LangChain OpenAI
- **ChromaDB** — Vector store for route/transit/traffic knowledge
- **LangSmith** — Distributed tracing and run monitoring
- **MLflow** — Experiment tracking and metrics logging
- **DeepEval** — Response quality evaluation (local + cloud)
- **Streamlit** — Interactive web UI
- **Plotly** — Charts, gauges, and map visualization

## PII Protection

All queries pass through the PII Guardian before processing:
- `EMAIL` → `[EMAIL REDACTED]`
- `PHONE` → `[PHONE REDACTED]`
- `SSN` → `[SSN REDACTED]`
- `CREDIT_CARD` → `[CARD REDACTED]`
- `HOME_ADDRESS` → `[ADDRESS REDACTED]`
- `PASSPORT` → `[PASSPORT REDACTED]`
- `DATE_OF_BIRTH` → `[DOB REDACTED]`
- `IP_ADDRESS` → `[IP REDACTED]`

Queries with HIGH-risk PII (SSN, credit card, passport) are blocked.
