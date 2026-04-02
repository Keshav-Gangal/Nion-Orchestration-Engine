# Nion Agentic Orchestration Engine

## 📌 Overview

This project implements a simplified version of Nion's AI orchestration engine, which processes incoming messages and generates a structured orchestration map across a multi-layer architecture (L1 → L2 → L3).

The system simulates how an AI Program Manager interprets communication, extracts insights, and coordinates execution across specialized agents.

---

## 🧠 Architecture

The system follows a **3-layer architecture**:

### 🔹 L1 (Planner)

* Performs intent analysis
* Identifies gaps and entities
* Generates a structured task plan

### 🔹 L2 (Router)

* Maps L1 tasks to appropriate L3 agents
* Enforces strict visibility rules

### 🔹 L3 (Agents)

* Execute specific tasks such as:

  * Action item extraction
  * Risk analysis
  * Issue tracking
  * Q&A responses

---

## ⚙️ Setup Instructions

1. Clone the repository:

```
git clone <your-repo-link>
cd <repo-name>
```

2. Ensure Python is installed (>= 3.10 recommended)

3. No external dependencies required

---

## ▶️ How to Run

### Run test cases:

```
python orchestrator.py
```

### Run a custom JSON file:

```
python orchestrator.py --file your_input.json
```

### Run inline JSON:

```
python orchestrator.py --json '{"message_id":"MSG-001", ... }'
```

---

## 📂 Project Structure

```
.
├── agent_registry.py
├── intent_analyzer.py
├── l1_planner.py
├── l2_router.py
├── output_formatter.py
├── orchestrator.py
├── test_cases.json
```

---

## 🧪 Sample Output

The system generates a full orchestration map including:

* L1 Plan
* L2 routing
* L3 execution outputs

Example outputs are included in:
`OUTPUT 6 TEST CASES.txt`

---

## ⚠️ Assumptions

* Input messages follow the provided JSON schema
* L3 outputs are simulated (not real AI models)
* Keyword-based routing is sufficient for this implementation
* Missing fields are handled via gap detection

---

## 🏗️ Design Decisions

* **Rule-based routing** for deterministic behavior
* **Layered architecture** to enforce visibility constraints
* **Dataclasses** used for structured data handling
* **Modular design** for easy extensibility

---

## 🚀 Future Improvements

* Replace keyword matching with NLP/ML models
* Add real-time data sources instead of simulated outputs
* Introduce scoring-based routing instead of first-match
* Add API interface for real-world usage

---

## ✅ Key Highlights

* Strict adherence to L1 → L2 → L3 visibility rules
* Dynamic task planning based on intent
* Clean separation of concerns across modules
* Fully testable using provided test suite

---

## 📎 Notes

This implementation is designed to closely follow the problem statement while keeping the system modular, readable, and extensible.
