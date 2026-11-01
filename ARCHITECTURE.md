# Architecture Overview
This document serves as a critical, living template designed to equip agents with a rapid and comprehensive understanding of the codebase's architecture, enabling efficient navigation and effective contribution from day one. Update this document as the codebase evolves.

## 1. Project Structure
This section provides a high-level overview of the project's directory and file structure, categorised by architectural layer or major functional area. It is essential for quickly navigating the codebase, locating relevant files, and understanding the overall organization and separation of concerns.

```
FatigueLab/
├── dashboard.py              # Frontend: Streamlit interactive UI & real-time Plotly charts
├── run_dashboard.bat         # Launcher: One-click Windows batch script
├── requirements.txt          # Dependencies: Core runtime packages (streamlit, plotly, openai, pandas)
├── test_run.py               # Testing: Standalone CLI verification harness
├── .env.example              # Config: Template for optional API keys
├── .gitignore                # Version Control: Exclusions for Python, cache, and report artifacts
├── LICENSE                   # Legal: Open-source MIT License
├── README.md                 # Documentation: Quickstart, features, and user guide
├── ABSTRACT.md               # Research: Formal hackathon/academic project abstract
├── ARCHITECTURE.md           # Architecture: System design, data flow, and components (this file)
│
├── config/                   # Target & Attack Configuration Layer
│   ├── scenarios.json        # 5 attack scenarios mapped to OWASP LLM vulnerability classes
│   └── targets.json          # 4 dynamic victim bot personas (Bank, IoT, Telecom, Retail)
│
├── core/                     # Multi-Agent Closed-Loop Engine
│   ├── __init__.py           # Package initialization
│   ├── attacker_agent.py     # 4-phase adversarial conversational attacker
│   ├── target_bot.py         # Configurable victim chatbot loader & context manager
│   ├── evaluator.py          # Safety evaluation, canary checks, and degradation metrics
│   └── llm_provider.py       # Unified LLM provider (OpenAI, Gemini, and Mock Simulation Engine)
│
└── reports/                  # Data Store: Generated JSON forensic audit reports
```

## 2. High-Level System Diagram
The system operates as an automated closed-loop multi-turn red-team harness with three autonomous agent components:

```
[User / Browser Interface] <---------------------> [Frontend: dashboard.py (Streamlit)]
                                                                  |
                      +-------------------------------------------+-------------------------------------------+
                      |                                           |                                           |
                      v                                           v                                           v
           [1. Attacker Agent]                         [2. Target Bot (Victim)]                    [3. Evaluator Bot]
        (core/attacker_agent.py)                       (core/target_bot.py)                       (core/evaluator.py)
                      |                                           |                                           |
                      | Generates Phase-Aware Message             | Processes Prompt with History             | Inspects Bot Response
                      | (Rapport -> Overload -> Authority)        | (Applies Persona & Domain Rules)          | (Canary, Policy, Prompt)
                      |                                           |                                           |
                      +--------------------> [LLM Client] <-------+                                           |
                                           (llm_provider.py)                                                  |
                                           /       |       \                                                  |
                              [OpenAI API]   [Gemini API]   [Mock Simulation]                                 |
                                                                                                              v
                                                          [Live Safety Degradation Curve & JSON Report] <-----+
```

## 3. Core Components

### 3.1. Frontend

Name: FatigueLab Streamlit Dashboard (`dashboard.py`)

Description: The central user interface that controls test parameters and visualizes live multi-turn conversations. It displays real-time safety degradation curves, phase transition indicators, box-plot score distributions, violation timelines, cross-run comparison overlays, and JSON forensic report download triggers.

Technologies: Python 3.10+, Streamlit, Plotly Graph Objects / Express, Pandas, Custom CSS

Deployment: Localhost web server (`http://localhost:8501`), containerized Docker instances, or cloud hosting (Streamlit Community Cloud / Cloud Run).

### 3.2. Backend Services & Agent Modules

#### 3.2.1. Adversarial Attacker Agent

Name: Phased Adversarial Attacker (`core/attacker_agent.py`)

Description: Simulates an evolving red-team customer or auditor who escalates conversation across 4 distinct psychological and semantic phases: Rapport Building, Context Overload, Authority Claim, and Direct Extraction. Progression limits dynamically scale according to user-selected aggression levels (Low, Medium, High).

Technologies: Python, FSM Phase Logic, LLM Prompt Engineering

Deployment: Embedded Python module within the evaluation runtime.

#### 3.2.2. Target (Victim) Bot Harness

Name: Swappable Target Bot Loader (`core/target_bot.py`)

Description: Acts as the chatbot under test. Instead of a single static chatbot, this component dynamically loads system prompts, planted confidential canary data, and domain policies from `config/targets.json`. It maintains conversation history to test attention dispersion and cognitive fatigue over prolonged context lengths.

Technologies: Python, JSON Schema Loader, Context Window Manager

Deployment: Embedded Python module within the evaluation runtime.

#### 3.2.3. Safety Evaluator & Metrics Engine

Name: Multi-Layered Safety Evaluator (`core/evaluator.py`)

Description: Evaluates every target bot reply per turn. Features deterministic regex pattern matching, planted canary string discovery, system prompt regurgitation checks, and numerical threshold validators (refund/credit/voucher limits). Computes per-turn Safety Score ($0–100$), cumulative Fatigue Index ($FI$), and standardized Resilience Grades ($A$ through $F$).

Technologies: Python, Regular Expressions (`re`), Heuristic Scoring Engine

Deployment: Embedded Python module within the evaluation runtime.

#### 3.2.4. Unified LLM Client & Simulation Engine

Name: LLM Client & Mock Engine (`core/llm_provider.py`)

Description: Abstraction layer managing communication with AI models. Supports live OpenAI API (`gpt-4o-mini`, `gpt-4o`), Google Gemini REST API (`gemini-1.5-flash`), and an integrated offline Mock Simulation Engine that produces realistic conversational fatigue curves without external API keys or costs.

Technologies: Python, `openai` Python SDK, `urllib.request`

Deployment: Embedded Python module within the evaluation runtime.

## 4. Data Stores

### 4.1. Configuration Store

Name: Scenario & Target Registries

Type: JSON Flat-Files (`config/scenarios.json`, `config/targets.json`)

Purpose: Stores definitions for attack scenarios (goals, OWASP categories, phase strategies) and target victim bots (personas, domain rules, confidential canary records, and policy thresholds).

Key Schemas:
- `scenarios.json`: `id`, `name`, `category`, `goal`, `phases` (name, strategy, target_turns)
- `targets.json`: `id`, `name`, `domain`, `system_prompt`, `rules_summary`, `secrets`, `forbidden_phrases`, `policy_thresholds`

### 4.2. Runtime Session & Report Repository

Name: In-Memory Session & Forensic Report Store

Type: Streamlit `st.session_state` (In-Memory) & JSON Files (`reports/*.json`)

Purpose: Holds the active conversation transcript, turn-by-turn scores, user-entered API keys, and exported forensic audit reports.

Key Schemas:
- `fatiguelab_report.json`: `scenario`, `goal`, `aggression`, `turns_run`, `broke_at_turn`, `fatigue_index`, `grade`, `scores`, `log` (turn, phase, attacker_msg, target_reply, violations)

## 5. External Integrations / APIs

Service Name 1: OpenAI API (`https://api.openai.com/v1/chat/completions`)
- Purpose: Generates live multi-turn attacker probes and live target chatbot responses using GPT-4o / GPT-4o-mini.
- Integration Method: Official `openai` Python SDK via user-supplied API key in the UI.

Service Name 2: Google Gemini REST API (`https://generativelanguage.googleapis.com/v1beta/models/`)
- Purpose: Generates live multi-turn attacker probes and target responses using Gemini 1.5 Flash / Pro.
- Integration Method: Direct HTTPS REST API (`urllib.request`) with no external SDK dependency.

Service Name 3: Offline Simulation Engine (Local Fallback)
- Purpose: Generates realistic multi-turn degradation responses locally for hackathon demos with zero API latency or cost.
- Integration Method: Native Python class within `core/llm_provider.py`.

## 6. Deployment & Infrastructure

Cloud Provider: Local Host (Windows, macOS, Linux) / Cloud-Agnostic

Key Services Used: Local Python runtime, Streamlit web server, optional Docker containerization

CI/CD Pipeline: GitHub repository with integrated command-line test verification (`python test_run.py`)

Monitoring & Logging: Real-time Plotly UI charting, in-app error notifications, and JSON audit logging

## 7. Security Considerations

Authentication: API keys are input interactively through the Streamlit UI and stored exclusively in browser session memory (`st.session_state`). Keys are **never** committed to Git, logged, or written to disk.

Synthetic Test Data: All customer records (Rahul Mehta, Priya Nair, Amit Sharma), credit card numbers, and system tokens are 100% synthetic/fake, preventing real-world data leaks.

Threat Model Alignment: Specifically addresses OWASP GenAI Top 10 risks:
- **LLM06: Sensitive Information Disclosure** (cross-customer PII leakage)
- **LLM07: System Prompt Leakage** (extracting internal developer rules)
- **LLM08: Excessive Agency** (bypassing monetary refund or physical unlock limits)

Network Isolation: Offline simulation mode operates with complete network isolation (no internet connection required).

## 8. Development & Testing Environment

Local Setup Instructions:
1. Clone the repository: `git clone https://github.com/YOUR_USERNAME/FatigueLab.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Launch dashboard: `streamlit run dashboard.py` (or double-click `run_dashboard.bat` on Windows)

Testing Frameworks: Custom CLI test runner (`test_run.py`) executing a full 12-turn simulated red-team cycle.

Code Quality Tools: Modular architecture, separation of concerns between agent roles, and strict PEP-8 standards.

## 9. Future Considerations / Roadmap

Semantic Evaluator Model: Integrating an LLM-as-a-Judge component for nuanced sentiment, compliance drift, and tone degradation detection.

Dynamic Target Endpoint Testing: Adding support for testing live external HTTP/WebSocket chatbot endpoints via webhook connectors.

Automated Guardrail Remediation: Automatically generating patched system prompts with periodic rule reinforcement based on the identified failure turn.

## 10. Project Identification

Project Name: FatigueLab (Adversarial Prompt Fatigue Tester for Conversational AI)

Repository URL: https://github.com/YOUR_USERNAME/FatigueLab

Primary Contact/Team: FatigueLab Core Research Team (Hackathon Track: AI & Cybersecurity)

Date of Last Update: 2026-11-01

## 11. Glossary / Acronyms

- **PII:** Personally Identifiable Information
- **CDR:** Call Detail Records (Telecom subscriber metadata)
- **OWASP:** Open Worldwide Application Security Project
- **FI (Fatigue Index):** Metric measuring the percentage drop between initial and final safety scores across dialogue turns
- **Canary:** A known unique token planted in system instructions to detect verbatim memory leakage
- **PyRIT:** Python Risk Identification Tool for Generative AI (Microsoft AI Red Team)
- **FSM:** Finite State Machine governing attacker phase transitions
