import os
import re
import sqlite3
import streamlit as st

from dotenv import load_dotenv
from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Natural Language to SQL",
    page_icon="🤖",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    BASE_DIR,
    "employee.db"
)

SCHEMA_PATH = os.path.join(
    BASE_DIR,
    "schema.txt"
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error(
        "GEMINI_API_KEY is missing.\n\n"
        "Please create a .env file and add:\n\n"
        "GEMINI_API_KEY=your_api_key_here"
    )
    st.stop()


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)

GEMINI_MODEL = "gemini-3.8-flash"


# ============================================================
# EXAMPLE QUESTIONS
# ============================================================

EXAMPLE_QUESTIONS = [
    "Show all employees",
    "Who is the oldest employee?",
    "Who is the youngest employee?",
    "Show me all data engineers",
    "Show me all data scientists",
    "What is the average age of employees?",
    "How many employees are in each designation?",
    "Show employees older than 30",
    "Show employees younger than 30",
    "Show employees sorted by age",
    "Show the oldest data scientist",
    "Show the youngest data engineer",
    "Find employees whose name starts with A",
]


# ============================================================
# GET DATABASE SCHEMA
# ============================================================

def get_schema_context():

    try:

        with open(
            SCHEMA_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()

    except FileNotFoundError:

        return """
Table: EMPLOYEE

Columns:
- EMP_NAME
- EMP_ID
- DESIGNATION
- EMP_AGE
"""


# ============================================================
# CHECK DATABASE
# ============================================================

def database_exists():

    return os.path.exists(DB_PATH)


# ============================================================
# SQL SAFETY VALIDATION
# ============================================================

def is_safe_query(sql_query):

    if not sql_query:
        return False

    query = sql_query.strip()

    query_upper = query.upper()

    # --------------------------------------------------------
    # Only SELECT queries
    # --------------------------------------------------------

    if not query_upper.startswith("SELECT"):

        return False

    # --------------------------------------------------------
    # Block multiple statements
    # --------------------------------------------------------

    cleaned_query = query.rstrip(";").strip()

    if ";" in cleaned_query:

        return False

    # --------------------------------------------------------
    # Dangerous SQL keywords
    # --------------------------------------------------------

    dangerous_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "ATTACH",
        "DETACH",
        "PRAGMA",
        "REPLACE",
        "VACUUM"
    ]

    for keyword in dangerous_keywords:

        pattern = r"\b" + re.escape(keyword) + r"\b"

        if re.search(
            pattern,
            query_upper
        ):

            return False

    # --------------------------------------------------------
    # Only allow EMPLOYEE table
    # --------------------------------------------------------

    tables = re.findall(
        r"\b(?:FROM|JOIN)\s+([A-Z_][A-Z0-9_]*)",
        query_upper
    )

    for table in tables:

        if table != "EMPLOYEE":

            return False

    return True


# ============================================================
# CLEAN GEMINI RESPONSE
# ============================================================

def clean_sql_response(sql_query):

    if not sql_query:

        return ""

    sql_query = sql_query.strip()

    # Remove markdown code blocks
    sql_query = sql_query.replace(
        "```sql",
        ""
    )

    sql_query = sql_query.replace(
        "```SQL",
        ""
    )

    sql_query = sql_query.replace(
        "```",
        ""
    )

    return sql_query.strip()


# ============================================================
# GEMINI SQL GENERATION
# ============================================================

def generate_sql_with_gemini(
    question,
    schema
):

    prompt = f"""
You are an expert SQLite SQL generator.

Your task is to convert the user's natural-language
question into a SQLite SELECT query.

DATABASE SCHEMA:
{schema}

IMPORTANT RULES:

1. Generate ONLY a SELECT statement.
2. Use ONLY the EMPLOYEE table.
3. Use only columns that exist in the schema.
4. Never generate INSERT.
5. Never generate UPDATE.
6. Never generate DELETE.
7. Never generate DROP.
8. Never generate ALTER.
9. Never generate CREATE.
10. Never generate TRUNCATE.
11. Never generate PRAGMA.
12. Never generate multiple SQL statements.
13. Do not modify the database.
14. Return ONLY the SQL query.
15. Do NOT use markdown code fences.
16. Do NOT explain the SQL.
17. Use SQLite-compatible syntax.

USER QUESTION:
{question}

Return only the SQL query.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    sql_query = response.text

    return clean_sql_response(
        sql_query
    )


# ============================================================
# GENERATE AND VALIDATE SQL
# ============================================================

def generate_sql_with_guardrails(question):

    schema = get_schema_context()

    try:

        sql_query = generate_sql_with_gemini(
            question,
            schema
        )

    except Exception as error:

        return (
            None,
            f"Gemini API error: {error}"
        )

    if not sql_query:

        return (
            None,
            "Gemini did not generate an SQL query."
        )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if not is_safe_query(sql_query):

        return (
            None,
            "The generated SQL failed the safety validation."
        )

    return (
        sql_query,
        None
    )


# ============================================================
# EXECUTE SQL
# ============================================================

def execute_query(sql_query):

    if not is_safe_query(sql_query):

        return (
            None,
            "Unsafe SQL query."
        )

    try:

        connection = sqlite3.connect(
            DB_PATH
        )

        cursor = connection.cursor()

        cursor.execute(
            sql_query
        )

        rows = cursor.fetchall()

        columns = [
            description[0]
            for description in cursor.description
        ]

        connection.close()

        return (
            {
                "columns": columns,
                "rows": rows
            },
            None
        )

    except Exception as error:

        return (
            None,
            str(error)
        )


# ============================================================
# SESSION STATE
# ============================================================

if "selected_question" not in st.session_state:

    st.session_state.selected_question = ""

if "generated_sql" not in st.session_state:

    st.session_state.generated_sql = ""

if "query_error" not in st.session_state:

    st.session_state.query_error = ""


# ============================================================
# HEADER
# ============================================================

st.title(
    "🤖 Natural Language to SQL Query Generator"
)

st.write(
    "Ask questions about employee data in natural language. "
    "Gemini converts your question into a safe SQLite SQL query."
)

st.info(
    "💡 Powered by Google Gemini API"
)


# ============================================================
# CHECK DATABASE
# ============================================================

if not database_exists():

    st.error(
        "employee.db was not found."
    )

    st.info(
        "Make sure employee.db is present in the project folder."
    )

    st.stop()


# ============================================================
# MAIN COLUMNS
# ============================================================

left_column, right_column = st.columns(
    [2, 1]
)


# ============================================================
# LEFT COLUMN
# ============================================================

with left_column:

    st.subheader(
        "💬 Ask Your Question"
    )

    question = st.text_area(
        "Enter your question:",
        value=st.session_state.selected_question,
        key="question_input",
        placeholder=(
            "Example: Who is the oldest employee?"
        ),
        height=120
    )

    st.subheader(
        "🤔 Try These Examples"
    )

    # --------------------------------------------------------
    # Example buttons
    # --------------------------------------------------------

    example_columns = st.columns(2)

    for index, example in enumerate(
        EXAMPLE_QUESTIONS
    ):

        with example_columns[
            index % 2
        ]:

            if st.button(
                example,
                key=f"example_{index}",
                use_container_width=True
            ):

                st.session_state.selected_question = (
                    example
                )

                st.session_state.generated_sql = ""

                st.session_state.query_error = ""

                st.rerun()

    st.write("")

    # --------------------------------------------------------
    # Generate SQL button
    # --------------------------------------------------------

    if st.button(
        "🚀 Generate SQL Query",
        type="primary",
        use_container_width=True
    ):

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            with st.spinner(
                "🤖 Gemini is generating SQL..."
            ):

                sql_query, error = (
                    generate_sql_with_guardrails(
                        question
                    )
                )

            if error:

                st.session_state.generated_sql = ""

                st.session_state.query_error = (
                    error
                )

                st.error(error)

            else:

                st.session_state.generated_sql = (
                    sql_query
                )

                st.session_state.query_error = ""

                st.success(
                    "SQL query generated successfully!"
                )


# ============================================================
# RIGHT COLUMN
# ============================================================

with right_column:

    st.subheader(
        "📊 Database Schema"
    )

    schema = get_schema_context()

    st.code(
        schema,
        language="text"
    )

    st.subheader(
        "🔒 Security"
    )

    st.write(
        "Only SELECT queries are allowed."
    )

    st.write(
        "Only the EMPLOYEE table can be accessed."
    )

    st.write(
        "Database modification queries are blocked."
    )


# ============================================================
# GENERATED SQL
# ============================================================

if st.session_state.generated_sql:

    st.markdown("---")

    st.subheader(
        "🔍 Generated SQL Query"
    )

    st.code(
        st.session_state.generated_sql,
        language="sql"
    )

    # --------------------------------------------------------
    # Execute SQL
    # --------------------------------------------------------

    if st.button(
        "▶️ Execute Query",
        type="secondary"
    ):

        with st.spinner(
            "Executing SQL query..."
        ):

            result, error = execute_query(
                st.session_state.generated_sql
            )

        if error:

            st.error(
                f"❌ Query execution failed: {error}"
            )

        else:

            st.subheader(
                "📈 Query Results"
            )

            columns = result["columns"]

            rows = result["rows"]

            if rows:

                table_data = []

                for row in rows:

                    table_data.append(
                        dict(
                            zip(
                                columns,
                                row
                            )
                        )
                    )

                st.dataframe(
                    table_data,
                    use_container_width=True,
                    hide_index=True
                )

                st.success(
                    f"✅ {len(rows)} row(s) returned."
                )

            else:

                st.info(
                    "The query executed successfully, "
                    "but no records were found."
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Natural Language → Gemini → SQL Validation → SQLite → Results"
)