# Academic Assignment Planning AI Agent 2.0

An advanced, intelligent cognitive scaffolding AI agent that transforms unstructured academic assignment prompts into feasible, constraint-satisfying, actionable study plans.

Aligned with coursework topics: **AI Agents, Agentic Workflows, Human-AI Interaction, AI Evaluation, Risk Management, and AI Safety**.

---

## 📁 Repository & File Structure

```text
d:\25PMC048\AI Agent\
├── server.py                   # Python Web Server & REST API backend (http://localhost:8000)
├── academic_planner_app.html   # Modern Glassmorphic Web Dashboard UI
├── academic_planner_app.py     # Core Python AI Agent, Validator & CLI Engine
├── test_academic_planner.py    # Automated Test Suite (Unittest)
├── requirements.txt            # Environment & Python dependencies (Standard Library)
└── README.md                   # Complete Project Documentation & Evaluation
```

---

## 🌟 What's New in Version 2.0:

1. **Modern SaaS Visual Design**:
   - Dark/Light Theme with glassmorphism and modern design tokens.
   - Dual-engine architecture: Automatically connects to `server.py` REST API when running, or falls back seamlessly to client-side agent logic when opened directly as a file.
   - Live Gantt Timeline view with protected safety buffer visualization.
   - Interactive milestone checklist that recalculates completion percentage in real time.
2. **True Python Backend Server (`server.py`)**:
   - Zero-dependency local HTTP server providing `/api/plan`, `/api/health`, and `/api/replan`.
3. **100% Working Actions**:
   - Preset loaders for Scenario 1 (Research Paper) and Scenario 2 (Coding Project).
   - Real-time Multi-Rule Guardrail feedback banner (Green on pass, Red on overload/inversion).
   - Dynamic Requirement Shift buttons: advance due date (-4 days) with automatic task compression and diff badge.
   - 1-click Markdown copy and JSON export.

---

## 🚀 How to Run and Test

### Option 1: Full-Stack Web App (Recommended)
1. In your terminal, start the Python backend server:
   ```powershell
   cd "d:\25PMC048\AI Agent"
   python server.py
   ```
2. Open your browser and navigate to:
   ```text
   http://localhost:8000
   ```
   *The green badge in the top right will show `🟢 Connected to Python Backend`.*

### Option 2: Standalone Local File (No Terminal Needed)
Double-click `academic_planner_app.html` in your file explorer or open it in any web browser. It runs with the embedded browser agent engine (`⚡ Local Browser Engine Active`).

### Option 3: Python Terminal CLI
```powershell
cd "d:\25PMC048\AI Agent"
python academic_planner_app.py
```

### Option 4: Automated Test Suite
```powershell
python -m unittest test_academic_planner.py
```

---

## 🎯 Syllabus Alignment & Architectural Summary

* **Agent Role**: Cognitive Scaffolding & Metacognitive Study Copilot.
* **Agentic Workflow**: Full **Perception $\rightarrow$ Task Decomposition $\rightarrow$ Constraint Scheduling $\rightarrow$ Multi-Rule Validation $\rightarrow$ Dynamic Re-planning** loop.
* **Guardrails & Verification**: Detects missing academic phases, dependency inversions, and workload capacity violations.
* **AI Safety & Ethics**: Scaffolding only; enforces student learning by generating verifiable *Definition of Done* criteria without ghostwriting essays or code.
