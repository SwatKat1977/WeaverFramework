"""
Copyright 2026 Weaver Framework Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import sqlite3
import logging
from typing import Any
import aiosqlite


class SqliteInterfaceException(Exception):
    """Exception for SQLite interaction errors."""


class SqliteInterface:
    """Async SQLite interface for database operations.

    This class provides a consistent interface for interacting with
    SQLite databases with configured connection settings, validation,
    and common query helper methods.

    Features include:
        - WAL journal mode for improved concurrency
        - Foreign key enforcement
        - Busy timeout configuration
        - Database file validation
        - Common CRUD helper methods
    """

    __slots__ = ["_db_filename", "_logger"]

    SQLITE_HEADER = b"SQLite format 3\x00"

    def __init__(self, logger: logging.Logger, db_filename: str) -> None:
        """Initialize the SQLite interface.

        Args:
            logger: Parent logger instance used to create a
                module-specific logger.
            db_filename: Path to the SQLite database file.
        """
        self._db_filename: str = db_filename
        self._logger = logger.getChild(__name__)

    #
    # ──────────────────────────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────────────────────────
    #

    def is_valid_database(self) -> bool:
        """Determine whether the database file is a valid SQLite database.

        Returns:
            True if the database file contains a valid SQLite header,
            otherwise False.
        """
        try:
            with open(self._db_filename, "rb") as file:
                return file.read(len(self.SQLITE_HEADER)) == self.SQLITE_HEADER
        except OSError:
            return False

    def ensure_valid(self) -> None:
        """Validate that the configured database file exists and is valid.

        Raises:
            SqliteInterfaceException: If the database file does not
                exist or is not a valid SQLite database.
        """
        if not os.path.exists(self._db_filename):
            raise SqliteInterfaceException("Database file does not exist")

        if not self.is_valid_database():
            raise SqliteInterfaceException("Database file format is not valid")

    #
    # ──────────────────────────────────────────────────────────────
    # Connection handling
    # ──────────────────────────────────────────────────────────────
    #

    async def _get_connection(self,
                              validate: bool = True) -> aiosqlite.Connection:
        """Create and configure an async SQLite database connection.

        The connection is configured with:
            - WAL journal mode
            - Foreign key enforcement
            - Busy timeout handling

        Args:
            validate: Whether to validate the database file before
                opening the connection.

        Returns:
            A configured async SQLite database connection.

        Raises:
            SqliteInterfaceException: If database validation fails.
        """
        if validate:
            self.ensure_valid()

        conn = await aiosqlite.connect(
            self._db_filename,
            timeout=5.0,
            detect_types=sqlite3.PARSE_DECLTYPES)

        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("PRAGMA journal_mode = WAL;")
        await conn.execute("PRAGMA busy_timeout = 5000;")

        return conn

    #
    # ──────────────────────────────────────────────────────────────
    # Core operations
    # ──────────────────────────────────────────────────────────────
    #

    async def create_table(self, schema: str, table_name: str) -> None:
        """Create a database table using the provided schema.

        Args:
            schema: SQL schema statement used to create the table.
            table_name: Name of the table being created.

        Raises:
            SqliteInterfaceException: If table creation fails.
        """
        conn = None

        try:
            conn = await self._get_connection(validate=False)

            await conn.execute(schema)
            await conn.commit()

        except sqlite3.Error as ex:
            raise SqliteInterfaceException(
                f"Create table failure for {table_name}: {ex}") from ex

        finally:
            if conn is not None:
                await conn.close()

    async def run_query(self,
                        query: str,
                        params: tuple = (),
                        fetch_one: bool = False,
                        commit: bool = False) -> Any:
        """Execute a SQL query.

        Args:
            query: SQL query string to execute.
            params: Query parameter values.
            fetch_one: Whether to return only a single row.
            commit: Whether to commit the transaction after execution.

        Returns:
            Query results, a single row, affected row count, or None
            depending on the query type and arguments provided.

        Raises:
            SqliteInterfaceException: If query execution fails.
        """
        conn = None

        try:
            conn = await self._get_connection()

            cursor = await conn.execute(query, params)

            if commit:
                await conn.commit()
                return cursor.rowcount

            if fetch_one:
                return await cursor.fetchone()

            if cursor.description:
                return await cursor.fetchall()

            return None

        except sqlite3.Error as ex:
            raise SqliteInterfaceException(f"Query error: {ex}") from ex

        finally:
            if conn is not None:
                await conn.close()

    async def insert_query(self,
                           query: str,
                           params: tuple = ()) -> int | None:
        """Execute an INSERT query.

        Args:
            query: SQL INSERT query string.
            params: Query parameter values.

        Returns:
            The row ID of the inserted record if available.

        Raises:
            SqliteInterfaceException: If the insert query fails.
        """
        conn = None

        try:
            conn = await self._get_connection()

            cursor = await conn.execute(query, params)

            await conn.commit()

            return cursor.lastrowid

        except sqlite3.Error as ex:
            raise SqliteInterfaceException(
                f"Insert query failed: {ex}") from ex

        finally:
            if conn is not None:
                await conn.close()

    async def bulk_insert_query(self,
                                query: str,
                                value_sets: list[tuple]) -> bool:
        """Execute a bulk INSERT query.

        Args:
            query: SQL INSERT query string.
            value_sets: List of parameter tuples to insert.

        Returns:
            True if the bulk insert operation succeeds.

        Raises:
            SqliteInterfaceException: If the bulk insert query fails.
        """
        conn = None

        try:
            conn = await self._get_connection()

            await conn.executemany(query, value_sets)

            await conn.commit()

            return True

        except sqlite3.Error as ex:
            raise SqliteInterfaceException(
                f"Bulk insert query failed: {ex}") from ex

        finally:
            if conn is not None:
                await conn.close()

    async def delete_query(self, query: str, params: tuple = ()) -> None:
        """Execute a DELETE query.

        Args:
            query: SQL DELETE query string.
            params: Query parameter values.

        Raises:
            SqliteInterfaceException: If the delete query fails.
        """
        conn = None

        try:
            conn = await self._get_connection()

            await conn.execute(query, params)

            await conn.commit()

        except sqlite3.Error as ex:
            raise SqliteInterfaceException(
                f"Delete query failed: {ex}") from ex

        finally:
            if conn is not None:
                await conn.close()

    async def run_script(self, query: str) -> None:
        """
        Execute schema/bootstrap SQL without database validation.
        """

        conn = None

        try:
            conn = await self._get_connection(validate=False)

            await conn.execute(query)

            await conn.commit()

        except sqlite3.Error as ex:
            raise SqliteInterfaceException(
                f"Schema query failed: {ex}") from ex

        finally:
            if conn is not None:
                await conn.close()
