## Project Pitch: AI Self‑Extending Engine

### 1. Vision & Mission
Create a **self‑extending AI engine** that can:
- Autonomously critique, refine, and evolve its own codebase
- Discover and integrate new languages, tools, and techniques
- Adapt continuously based on user‑defined goals and real‑world metrics

This project explores the boundaries of AI‑driven software development, demonstrating how an intelligent agent can bootstrap, improve, and diversify its own capabilities over time.

---

### 2. Core Objectives
1. **Foundational Loop:** Implement a minimal, robust "critique → refine" cycle powered by a free Gemini API key.
2. **Directive‑Driven Behavior:** Use a unified configuration schema to define goals, priorities, and role sequences.
3. **Self‑Review & Metrics:** Integrate test generation, execution, and self‑assessment to validate improvements.
4. **Modular Architecture:** Build plugin interfaces for new languages, testing frameworks, and analysis tools.
5. **Growth & Autonomy:** Enable dynamic discovery of additional roles and plugins as the engine matures.

---

### 3. Key Features & Components
- **Engine Core:** Orchestrator managing rounds of improvement and evaluating results.
- **Roles & Plugins:** Abstract classes for Critique, Refine, Test Generation, Self‑Review, plus language adapters.
- **Configuration:** Single YAML/JSON file prescribing role order, model settings, thresholds, and directives.
- **Snapshot Store:** Versioned history of code, critiques, patches, and decisions for auditability.
- **Metrics Dashboard:** Track lint scores, test coverage/pass rate, autonomy level, and plugin count.
- **CLI & UI:** Command‑line interface initially, with a future Streamlit/Textual dashboard for visualizing rounds.

---

### 4. Architectural Overview
1. **CLI Entry Point (`__main__.py`):** Parses config, loads initial code/task, and invokes the Engine.
2. **Engine (`engine.py`):** Iterates through configured Role sequence, manages loop counts, and triggers snapshotting.
3. **Role Classes (`roles/`):** Each role implements `run(context) → context`:
   - **CritiqueRole:** Analyze code, generate critique.
   - **RefineRole:** Apply patches based on critique.
   - **TestGenRole:** Create and run tests.
   - **SelfReviewRole:** Assess refinements, decide acceptance.
4. **Plugin Modules (`plugins/`):** Language and tool adapters implementing detection, execution, and testing.
5. **Memory & Snapshots (`memory/`):** Store round metadata, code versions, critiques, and test results.
6. **Metrics & Decision Logic:** Calculate performance and feed back into loop termination or role injection.

---

### 5. Roadmap & Phases
| Phase | Goals & Deliverables                                              | Rough Timeline |
|-------|-------------------------------------------------------------------|----------------|
| 1     | MVP: Python Critique→Refine CLI, basic config, snapshotting       | Weeks 1–2      |
| 2     | Add Self‑Review & TestGen roles, seed tests, basic metrics        | Weeks 3–4      |
| 3     | Modular plugin API & PythonPlugin: lint, pytest integration       | Weeks 5–6      |
| 4     | UI Dashboard for rounds, extensible config for custom roles       | Weeks 7–8      |
| 5     | Discovery: auto‑detect new languages/tools, dynamic plugin loader | Weeks 9–12     |

---

### 6. Success Criteria & Metrics
- **Stability:** Engine runs 5+ loops without errors
- **Quality Improvement:** Measurable reduction in lint errors and increased test pass rates
- **Autonomy:** SelfReviewRole accepts patches without human intervention in ≥80% of cases
- **Extensibility:** Ability to integrate a new language plugin (e.g., JavaScript) with minimal code changes

---

### 7. Immediate Next Steps
1. **Review Deep‑Dive Modules:** Start with `run_improvement.py` to extract the core loop.
2. **Finalize Config Schema:** Merge existing schemas into a unified `config.yaml`.
3. **Scaffold Project Structure:** Create initial package layout and README.
4. **Implement MVP Engine & CritiqueRole:** Use existing prompt templates and logging.
5. **Schedule Checkpoints:** Bi‑weekly demos and retrospectives.

---

*Let me know any feedback or additions, and then we can dive into the first deep‑dive!*

