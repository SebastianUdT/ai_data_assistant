"""
Production Database Configuration

PURPOSE
-------
Own the application's database location and database initialization.

ARCHITECTURE
------------

Application
    ↓
Repository
    ↓
Database configuration
    ↓
SQLite


WHY THIS FILE EXISTS
--------------------
Database configuration should not be scattered through:

- agents
- tools
- services
- CLI scripts

The rest of the application should not need to know where the
SQLite file lives or how the schema is initialized.


PRODUCTION
----------
SQLite is useful for learning and small local applications.

A larger production system would commonly replace this infrastructure
with PostgreSQL, Supabase, or another durable database.

The important architecture remains:

    Service
        ↓
    Repository
        ↓
    Database
"""

import sqlite3
from pathlib import Path


# =====================================================================
# DATABASE LOCATION
# =====================================================================


DATABASE_PATH = (
    Path(__file__).parent
    / "data"
    / "finance.db"
)


# =====================================================================
# CONNECTION
# =====================================================================


def get_connection() -> sqlite3.Connection:
    """
    Create one SQLite database connection.

    The repository owns the lifetime of individual connections for now.

    PRODUCTION
    ----------
    PostgreSQL applications commonly use a connection pool instead of
    creating direct connections like this.
    """

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    # Return rows that support:
    #
    #     row["balance"]
    #
    # instead of relying only on numeric indexes.
    connection.row_factory = sqlite3.Row

    return connection


# =====================================================================
# SCHEMA INITIALIZATION
# =====================================================================


def initialize_database() -> None:
    """
    Create the database schema if it does not already exist.

    IMPORTANT
    ---------
    CREATE TABLE IF NOT EXISTS is enough for this reference project.

    Production systems normally use migrations:

        Alembic
        SQL migration files
        Supabase migrations
        framework migration systems

    because production schemas evolve over time.
    """

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                balance REAL NOT NULL
            )
            """
        )


# =====================================================================
# DEVELOPMENT SEED
# =====================================================================


def seed_database() -> None:
    """
    Insert our reference customers without overwriting existing data.

    CHECK
    -----
    INSERT OR IGNORE is deliberate.

    If customer_001 already has a modified balance, restarting the
    application must NOT reset it to 2500.
    """

    initialize_database()

    with get_connection() as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO customers (
                customer_id,
                balance
            )
            VALUES (?, ?)
            """,
            [
                (
                    "customer_001",
                    2500.00,
                ),
                (
                    "customer_002",
                    1800.00,
                ),
            ],
        )