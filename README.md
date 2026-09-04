# OpsPilot — AI Operations Copilot

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)

**OpsPilot** is an enterprise-grade Operations Intelligence and Workflow Platform. It enables business and operations leaders to inspect company operational data, detect systemic anomalies, answer questions using verified SQL and policy documents, generate prioritized action plans, and safely execute approved operational workflows.

OpsPilot is **not a generic chatbot** — it is an operations engine combining deterministic business rules, strict read-only AST-validated SQL, statistical anomaly detection, local RAG with verifiable page citations, and human-in-the-loop approvals.

---

## Key Highlights

- **Multi-Source Data Ingestion:** Native support for CSV, Excel (.xlsx multi-sheet), JSON arrays, SQLite database files, and PostgreSQL connections.
- **Deterministic Profiling & Semantic Catalog:** Auto-detects column roles, null ratios, cardinality, business entities, and foreign-key relationships with confidence scores.
- **Strict Read-Only SQL Safety Layer:** AST parsing with statement whitelisting (SELECT, WITH, EXPLAIN), comment stripping, multi-query rejection, result row limits, and table whitelisting.
- **KPI & Period Comparison Engine:** Standardized operational KPIs (Revenue, Late Delivery Rate, Overdue Aging, SLA Breach Rate) with sparklines and period-over-period drift.
- **Deterministic Business Rules & Exceptions:** Visual rule engine evaluating conditions (ge > 45 AND amount > 10000) and ranking operational exceptions by transparent priority formulas.
- **Local RAG & Verifiable Citations:** Index SOPs, refund policies, and SLAs (PDF, DOCX, TXT, MD) with chunk-level metadata and page citations.
- **Hybrid SQL + Policy Reasoning:** Unifies structured data queries with unstructured company policy requirements.
- **Human-in-the-Loop Action Center:** Proposes discrete operational actions with a mandatory review/approval gate, safe local execution, and tamper-evident audit logging.
- **One-Click Morning Review:** Automated daily routine that evaluates rules, detects anomalies, monitors SLAs, and synthesizes an executive operations brief.
- **Comprehensive Benchmarks:** Ground-truth test suites covering SQL precision, policy retrieval recall, and hybrid question reasoning.

---

## Architecture Summary

`
Frontend (React + Vite + Tailwind + Recharts)
   ?
FastAPI Backend (Pydantic v2 + SQLAlchemy + SQLite Audit)
   ?
Operations Copilot Orchestrator (Gemini 3.8 Flash / Tool Planner)
   +-- SQL Tool (AST Read-Only Enforcer)
   +-- DataFrame Analytics Tool (Pandas)
   +-- KPI Engine (Drift & Thresholds)
   +-- Business Rule Engine (Deterministic)
   +-- Anomaly Tool (Z-Score, IQR, Rolling Deviation)
   +-- RAG Tool (Local Vector Index & Page Citations)
   +-- Action Center Engine (Human Approval Gate)
   +-- Report Tool (OpenPyXL Excel & CSV/JSON Generator)
`

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### One-Command Launch
`ash
# Clone the repository
git clone https://github.com/danial-maqbool/AI-Operations-Copilot.git
cd AI-Operations-Copilot

# Setup environment
cp .env.example .env

# Run unified launcher
python run.py
`

Open [http://localhost:8000](http://localhost:8000) to access OpsPilot.

---

## Documentation

- [Architecture & Design Details](docs/ARCHITECTURE.md)
- [Copilot Orchestration & Tool Protocols](docs/COPILOT.md)
- [Data Safety & Security Protocols](docs/DATA_SAFETY.md)
- [Recruiter 5-Minute Demo Walkthrough](docs/DEMO.md)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
