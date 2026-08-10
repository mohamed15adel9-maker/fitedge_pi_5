
import re

from memory.database import get_connection


FORBIDDEN = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "pragma",
    "attach",
    "detach",
    "replace",
}


def execute_query(sql):
    """
    Execute a read-only SQLite SELECT query.

    Only SELECT statements are allowed.
    SQL keywords are checked as complete tokens so that
    legitimate column names such as 'created_at' are allowed.
    """

    if not sql or not isinstance(sql, str):
        return (
            "Invalid SQL query. "
            "Please provide a valid SQL SELECT statement."
        )

    cleaned = sql.strip().rstrip(";").strip()

    if not cleaned:
        return "Invalid SQL query."

    # ---------------------------------------------------------
    # ONLY SELECT
    # ---------------------------------------------------------

    if not re.match(r"^select\b", cleaned, re.IGNORECASE):
        return "ERROR: only SELECT queries are allowed."

    # ---------------------------------------------------------
    # NO MULTIPLE STATEMENTS
    # ---------------------------------------------------------

    if ";" in cleaned:
        return "ERROR: multiple SQL statements are not allowed."

    # ---------------------------------------------------------
    # FORBIDDEN SQL KEYWORDS
    # ---------------------------------------------------------

    # Match complete SQL keywords only.
    #
    # This allows:
    #
    #     created_at
    #     updated_at
    #     deleted_at
    #
    # while blocking:
    #
    #     CREATE
    #     UPDATE
    #     DELETE
    #     DROP
    #     ALTER
    #     INSERT
    #
    sql_lower = cleaned.lower()

    for word in FORBIDDEN:

        pattern = rf"\b{re.escape(word)}\b"

        if re.search(pattern, sql_lower):
            return (
                f"Forbidden SQL operation detected: {word}. "
                "Only SELECT queries are allowed."
            )

    # ---------------------------------------------------------
    # EXECUTE
    # ---------------------------------------------------------

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(cleaned)

        rows = cursor.fetchall()

        connection.close()

    except Exception as e:

        return f"ERROR running query: {e}"

    # ---------------------------------------------------------
    # NO RESULTS
    # ---------------------------------------------------------

    if not rows:
        return "No results found."

    # ---------------------------------------------------------
    # FORMAT RESULTS
    # ---------------------------------------------------------

    result_lines = []

    for row in rows:

        row_dict = dict(row)

        line = ", ".join(
            f"{key}: {value}"
            for key, value in row_dict.items()
        )

        result_lines.append(line)

    return "\n".join(result_lines)

