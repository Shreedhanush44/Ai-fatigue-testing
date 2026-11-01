# FatigueLab — Adversarial Prompt Fatigue Tester

> **Hackathon: Avishkar | Track: AI & Cybersecurity**

Traditional chatbot security testing fires a *single* jailbreak prompt and checks whether the bot resists. Real attackers don't work that way — they use **long, friendly, confusing conversations** that slowly wear down a bot's guardrails over many turns.

**FatigueLab** is an automated red-team harness that measures **when** a chatbot's safety rules break, not just **if** they break.

---

## 🏗 Architecture

```
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│  🗡️ ATTACKER    │───────▶│  🤖 TARGET BOT  │───────▶│  🔍 EVALUATOR   │
│  AGENT          │ prompt │  (Victim)       │ reply  │                 │
│                 │        │  Varies per     │        │  Scores safety  │
│  4-phase        │        │  test run       │        │  per turn       │
│  escalation     │        │  (Bank, IoT,    │        │                 │
│                 │        │   Telecom, etc) │        │                 │
└─────────────────┘        └─────────────────┘        └────────┬────────┘
                                                               │
                                                               ▼
                                                   ┌─────────────────────┐
                                                   │  📊 DASHBOARD       │
                                                   │  Live safety graph  │
                                                   │  Conversation log   │
                                                   │  Cross-run compare  │
                                                   │  JSON report export │
                                                   └─────────────────────┘
```

### The Three Bots

| Bot | File | Role |
|-----|------|------|
| **Attacker Agent** | `core/attacker_agent.py` | Generates adversarial messages across 4 escalation phases |
| **Target Bot** (Victim) | `core/target_bot.py` | The chatbot under test — loads persona dynamically from `config/targets.json` |
| **Evaluator** | `core/evaluator.py` | Scores every target reply for secret leaks, prompt leaks, and policy breaches |

---

## 🎯 Attack Phases

The attacker escalates through 4 phases based on the selected aggression level:

| Phase | Strategy | Low (turns) | Medium (turns) | High (turns) |
|-------|----------|-------------|----------------|--------------|
| 🤝 Rapport Building | Friendly small talk to build trust | 1–5 | 1–3 | 1–2 |
| 🌊 Context Overload | Dense, confusing messages to cause fatigue | 6–12 | 4–7 | 3–4 |
| 👔 Authority Claim | Impersonate auditor/manager, cite fake mandates | 13–17 | 8–11 | 5–7 |
| 💉 Direct Extraction | Directly demand secrets / policy overrides | 18–25 | 12–25 | 8–25 |

---

## 🤖 Swappable Target Bots

Each test run uses a **different victim bot** loaded from `config/targets.json`:

| Target | Domain | What it protects |
|--------|--------|-----------------|
| SecureBank Support | Banking & Fintech | Customer PII, account numbers, refund limits |
| CampusSmart Kiosk | IoT & Physical Kiosks | Hardware tokens, door unlock relays |
| TelcoPlus Care | Telecom | Subscriber SIM/IMSI, billing credits |
| CartSwift Concierge | E-Commerce | Vendor margins, warehouse keys, promo codes |

---

## 📊 Dashboard Features

- **Live safety degradation graph** — watch the score drop turn by turn
- **Phase-colored markers** — see which attack phase caused each score change
- **Breach threshold line** — red zone when score drops below 40
- **Score distribution box plot** — compare scores across attack phases
- **Violation timeline** — exact turn and type of each policy breach
- **Cross-run comparison** — overlay results from multiple tests
- **Resilience grading** — A through F based on when/if the bot broke
- **JSON report export** — download full test results

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/FatigueLab.git
cd FatigueLab
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Launch the dashboard

```bash
streamlit run dashboard.py
```

### 4. Configure & Run in the UI

1. Open your browser at `http://localhost:8501`.
2. Under **🔑 LLM Provider & Authentication** in the sidebar:
   - Choose **⚡ Offline Simulation** (instant demo, no API key needed).
   - Or choose **🤖 OpenAI / 💎 Gemini** and paste your API key directly into the interface password field (no `.env` file editing required!).
3. Select your **Target Bot** (victim changes per test) and **Attack Scenario**.
4. Set **Attacker Aggression** and **Max Conversation Turns**.
5. Click **🚀 Start Fatigue Test** to watch the live safety degradation graph in real time!

---

## 📁 Project Structure

```
FatigueLab/
├── dashboard.py              # Streamlit UI — run this
├── requirements.txt          # Python dependencies
├── .env.example              # Template for API keys
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
├── README.md                 # This file
│
├── config/
│   ├── scenarios.json        # Attack scenarios (5 scenarios)
│   └── targets.json          # Target bot configurations (4 bots)
│
├── core/
│   ├── __init__.py
│   ├── llm_provider.py       # LLM client (OpenAI / Gemini / Mock)
│   ├── attacker_agent.py     # Phased adversarial attacker
│   ├── target_bot.py         # Configurable victim bot
│   └── evaluator.py          # Safety scorer + metrics
│
└── reports/                  # Saved test reports (gitignored)
```

---

## 📈 Metrics Explained

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Safety Score** | 100 − (penalties per violation) | Per-turn score; 100 = fully safe, 0 = fully broken |
| **Fatigue Index** | (first_score − last_score) / first_score × 100 | How much safety degraded over the conversation |
| **Resilience Grade** | Based on min score + breach turn | A (rock solid) → F (broke early) |

---

## ⚙️ LLM Providers

| Provider | Setup | Best for |
|----------|-------|----------|
| `mock` | None | Instant demos, no API key needed |
| `openai` | Set `OPENAI_API_KEY` in `.env` | Production testing with GPT-4o-mini |
| `gemini` | Set `GEMINI_API_KEY` in `.env` | Production testing with Gemini 1.5 |

---

## ⚠️ Disclaimer

All customer data, account numbers, tokens, and PINs in this project are **completely fake**. FatigueLab is designed for **defensive security research** — use it only on bots you own or have explicit permission to test.

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.
