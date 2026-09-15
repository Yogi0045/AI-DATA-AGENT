# AI Data Agent 🤖

An **Agentic AI Data Analyst** that allows users to interact with databases and data files using natural language.

The project uses **LLMs, LangGraph, PostgreSQL, and Python** to automate two major workflows:

* **SQL Analysis** — Converts natural-language questions into SQL queries, validates them, executes them against PostgreSQL, and generates a human-readable answer.
* **ETL Analysis** — Reads CSV data, understands the requested transformation, applies the transformation, and saves the processed data as a new CSV file.

## 🚀 Architecture

```text
                    User
                      │
                      ▼
                ┌───────────┐
                │ Data Agent│
                └─────┬─────┘
                      │
             ┌────────┴────────┐
             ▼                 ▼
      ┌──────────────┐  ┌──────────────┐
      │ SQL Analyst  │  │ ETL Analyst  │
      └──────┬───────┘  └──────┬───────┘
             │                  │
             ▼                  ▼
        PostgreSQL          CSV Files
             │                  │
             ▼                  ▼
        SQL Result       Transformed Data
             │                  │
             └────────┬─────────┘
                      ▼
                 Final Answer
```

## 🧠 SQL Analyst

The SQL workflow:

1. Receives a natural-language question.
2. Curates the question for better SQL generation.
3. Provides the database schema and sample data to the LLM.
4. Generates a PostgreSQL query.
5. Checks whether the query is safe.
6. Executes the query.
7. Converts the result into a human-readable response.

### Example

**User:**

> What are the payment methods available in the database?

**Generated SQL:**

```sql
SELECT DISTINCT payment_method
FROM payments
LIMIT 10;
```

**Result:**

```text
debit_card
credit_card
google_pay
apple_pay
paypal
```

## 🔄 ETL Analyst

The ETL workflow allows the agent to transform CSV data based on natural-language instructions.

For example:

> Filter the data to show Bulbasaur Pokémon only.

The agent reads the source CSV, applies the transformation, and saves the result into the transformation directory.

```text
data/
├── extract/
│   └── extracted_data.csv
└── transform/
    └── filtered_bulbasaur.csv
```

## 🛠️ Tech Stack

* **Python**
* **LangGraph**
* **LangChain**
* **PostgreSQL**
* **Pandas**
* **LLM APIs**
* **uv**
* **Pydantic**

## 📁 Project Structure

```text
AI-Data-Agent/
│
├── agents/
│   ├── data_agent.py
│   ├── sql_analyst.py
│   ├── etl_analyst.py
│   └── scratch.py
│
├── data/
│   ├── extract/
│   └── transform/
│
├── models/
│   └── schema.py
│
├── utils/
│   ├── database.py
│   ├── etl_tools.py
│   └── llm_pick.py
│
├── main.py
├── feed_db.py
├── pyproject.toml
└── uv.lock
```

## 🎯 What This Project Demonstrates

* Agentic AI workflows
* LLM tool calling
* LangGraph state management
* Natural-language-to-SQL generation
* SQL safety validation
* PostgreSQL database interaction
* Automated ETL workflows
* CSV data transformation
* Multi-step AI reasoning workflows

## 📌 Future Improvements

* Support for more file formats such as Excel and JSON
* More ETL transformation tools
* Database write operations with approval mechanisms
* RAG-based data documentation
* Multi-agent orchestration
* Web-based interface
* Improved query validation and error recovery
