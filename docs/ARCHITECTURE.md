# OpsPilot Architecture Documentation

OpsPilot is an AI Operations Copilot and operational intelligence SaaS platform designed to inspect operational data, detect problems, answer business questions, produce prioritized action lists, and execute human-approved workflows.

---

## 1. System Overview

`mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        UI["React 18 + TypeScript + Vite + Tailwind CSS"]
        CP["Copilot Chat & Evidence Inspector"]
        DS["Data Source Manager & Profiler"]
        AC["Action Approval Center"]
        WF["Workflow Studio"]
        EX["Exceptions & SLA Monitor"]
        KB["Document Knowledge Base (RAG)"]
        RP["Report Generator (Excel/CSV/JSON)"]
    end

    subgraph API ["API & Gateway (FastAPI)"]
        Router["FastAPI REST & Streaming Router"]
        Safety["SQL Safety & Read-Only Validator (AST Parser)"]
        Audit["Audit Logger & Execution Tracker"]
        PII["PII Redaction & Data Minimizer"]
    end

    subgraph Core ["Operations Intelligence Core"]
        Orch["Operations Copilot Orchestrator"]
        Planner["Intent Classification & Bounded Tool Planner"]
        
        subgraph Tools ["Deterministic & Analysis Tools"]
            ToolSQL["Safe SQL Analysis Tool"]
            ToolDF["Pandas In-Memory Analytics Tool"]
            ToolKPI["KPI Engine & Period Comparison"]
            ToolRule["Deterministic Business Rule Engine"]
            ToolAnomaly["Statistical Anomaly Detector (Z-Score/IQR/Rolling)"]
            ToolRAG["Document RAG & Citation Retriever"]
            ToolAction["Action Proposal & Approval Gate Engine"]
            ToolReport["Executive Reporting Engine (OpenPyXL)"]
        end

        Val["Result Grounding & Assertion Validator"]
        Composer["Response Composer & Confidence Calculator"]
    end

    subgraph Storage ["Persistence Layer"]
        InternalDB[("Internal SQLite Database (Alembic)")]
        VectorStore[("Local Vector Index (Chroma/Cosine Embeddings)")]
        ExternalData[("External Sources: CSV / XLSX / JSON / SQLite / Postgres")]
    end

    UI --> Router
    Router --> Safety
    Router --> Orch
    Orch --> Planner
    Planner --> Tools
    ToolSQL --> ExternalData
    ToolDF --> ExternalData
    ToolRAG --> VectorStore
    Tools --> Val
    Val --> Composer
    Composer --> Router
    ToolAction --> AC
    AC --> Audit
    Audit --> InternalDB
