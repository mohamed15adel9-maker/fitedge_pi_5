import sqlite3
from pathlib import Path

from memory.schema import SCHEMA

ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = ROOT / "memory.db"


def get_connection():
    """
    Opens a connection to the SQLite database.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    # Return rows as dictionaries instead of tuples
    connection.row_factory = sqlite3.Row

    # Enable foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def initialize_database():
    """
    Creates all database tables if they do not already exist.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.executescript(SCHEMA)

    connection.commit()

    connection.close()

    print("Database initialized successfully.")