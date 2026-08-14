from memory.database import get_connection

def execute_query(sql):
    if not sql or not isinstance(sql, str):
        return "Invalid SQL query. Please provide a valid SQL SELECT statement."
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned.lower().startswith("select"):
        return "ERROR: only SELECT queries are allowed."
    FORBIDDEN = ["insert", "update", "delete", "drop", "alter", "create"]
    for word in FORBIDDEN:
        if word in sql.lower():
            return f"Forbidden SQL operation detected: {word}. Only SELECT statements are allowed."
    if ";" in cleaned:
        return "ERROR: multiple statements are not allowed."
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(cleaned)
        rows = cursor.fetchall()
        connection.close()
    except Exception as e:
        return f"ERROR running query: {e}"

    if not rows:
        return "No results found."

    # Format rows as readable text for the LLM
    result_lines = []
    for row in rows:
        row_dict = dict(row)
        line = ", ".join(f"{key}: {value}" for key, value in row_dict.items())
        result_lines.append(line)

    return "\n".join(result_lines)    