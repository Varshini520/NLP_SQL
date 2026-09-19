# Natural Language to SQL Q&A

A Streamlit application that converts plain-English employee questions into safe SQLite `SELECT` queries and displays the results.

## Features
- Natural-language employee queries
- No OpenAI API key or API credits required
- Safe read-only SQL generation
- SQLite database
- Interactive Streamlit results table
- Example questions for quick testing

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python sql_data_insert.py
python -m streamlit run sql_app.py
```

Then open `http://localhost:8501`.

## Example questions
- Who is the oldest employee?
- Who is the youngest data scientist?
- What is the average age of employees?
- How many employees are in each designation?
- Show employees older than 30
- Show employees sorted by age
- Find employees with name starting with 'A'

## Security
Do not commit `.env` or API keys to GitHub. The default version of this project does not require an external API key.
