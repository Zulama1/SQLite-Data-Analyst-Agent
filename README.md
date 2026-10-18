# Minimal SQLite Data Analyst Agent From Scratch

A zero-framework autonomous agent loop built with Python and the official Google GenAI SDK. 

Instead of wrapping interactions in third-party orchestration frameworks like LangChain or LangGraph, this project aims to demonstrate how agentic behavior(schema discovery, query planning, iterative tool execution, and error self-correction) works directly on bare metal.



## Architecture Overview

```
User Prompt
│
▼
[Agent Turn Loop] ◄────────────────────────────────────┐
│                                                      │
▼                                                      │
Gemini 3.8 Flash                                       │
│                                                      │
├── Tool Request: get_schema()                         │
│        └─► Read sqlite_master ───────────────────────┤
│                                                      │
├── Tool Request: run_query(sql)                       │
│        ├─► [Success] Return JSON rows ───────────────┤
│        └─► [Error] Feed SQLite exception back ───────┤ (Self-Correction)
│                                                      │
└── Final Answer (No tools requested)                  │
│                                                      │
└─► Output text to user ───────────────────────────────┘

```

The agent runs in a bounded execution loop (`max_steps=10`) with `automatic_function_calling` intentionally disabled:
1. **Dynamic Schema Discovery:** Rather than injecting raw schemas into the system prompt upfront, the agent discovers tables and constraints using `get_schema()`.
2. **Execution & Self-Correction:** When SQLite throws an error (e.g., syntax mistakes or hallucinated columns), the exception string is sent straight back into the conversation context as a tool response. The model inspects the error message and rewrites the query automatically.
3. **Synthesis:** Once valid data rows are obtained, the model formats the findings and terminates the loop.



## Project Structure

```text
sqlite-analyst-agent/
│
├── .env.example                        # API key
├── .gitignore                          # Goated
├── requirements.txt                    # Python requirements
├── ecommerce_testing_dataset.xlsx      # Sample database records
├── setup_db.py                         # Ingestion script to build dataset.db
└── agent.py                            # Core agent loop and tool definitions

```

---

## Getting Started

### 1. Prerequisites

* Python 3.10+
* A Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone [https://github.com/](https://github.com/)<your-username>/sqlite-analyst-agent.git
cd sqlite-analyst-agent

python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```bash
GEMINI_API_KEY=your_gemini_api_key_here

```

### 4. Database Setup

Generate `dataset.db` from the sample spreadsheet:

```bash
python -m setup_db

```

### 5. Run the Agent

Execute the main agent script:

```bash
python -m agent

```

---

## Example Trace

Query: `"Who are the top 3 customers who ordered most recently?"`

```text
[Step 1] Calling tool: get_schema({})
       Result: CREATE TABLE customers (customer_id INTEGER, full_name TEXT, email TEXT, signup_date DATE, country TEXT)...

[Step 2] Calling tool: run_query({'query': 'SELECT c.customer_id, c.full_name, MAX(o.order_date) AS most_recent_order_date FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.full_name ORDER BY most_recent_order_date DESC LIMIT 3;'})
       Result: {"columns": ["customer_id", "full_name", "most_recent_order_date"], "rows": [[1, "Alice Morgan", "2024-06-30"], [14, "Noah Miller", "2024-06-29"], [19, "Sofia Gomez", "2024-06-27"]]}

Final Answer:
The top 3 customers who ordered most recently are:
1. Alice Morgan (Customer ID: 1) – Most recent order date: 2024-06-30
2. Noah Miller (Customer ID: 14) – Most recent order date: 2024-06-29
3. Sofia Gomez (Customer ID: 19) – Most recent order date: 2024-06-27

```

