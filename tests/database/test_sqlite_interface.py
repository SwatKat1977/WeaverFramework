import logging
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from weaver_framework.database.sqlite_interface import (
    SqliteInterface,
    SqliteInterfaceException
)


class TestSqliteInterface(unittest.TestCase):

    def setUp(self):

        self._temp_file = tempfile.NamedTemporaryFile(
            suffix=".db",
            delete=False
        )

        self._temp_file.close()

        self._logger = logging.getLogger("test")

        self._interface = SqliteInterface(
            self._logger,
            self._temp_file.name
        )

    def tearDown(self):

        try:
            os.unlink(self._temp_file.name)

        except (PermissionError, FileNotFoundError):
            pass

    def _initialize_database(self) -> None:

        conn = sqlite3.connect(self._temp_file.name)

        conn.execute(
            "CREATE TABLE test(id INTEGER)"
        )

        conn.commit()
        conn.close()

    #
    # Validation
    #

    def test_is_valid_database_returns_false_for_empty_file(self):

        self.assertFalse(
            self._interface.is_valid_database()
        )

    def test_is_valid_database_returns_true_for_valid_database(self):
        self._initialize_database()

        self.assertTrue(
            self._interface.is_valid_database()
        )

    def test_ensure_valid_raises_for_missing_database(self):

        os.unlink(self._temp_file.name)

        with self.assertRaises(SqliteInterfaceException):
            self._interface.ensure_valid()

    def test_ensure_valid_raises_for_invalid_database(self):

        with self.assertRaises(SqliteInterfaceException):
            self._interface.ensure_valid()

    #
    # Connection
    #

    def test_get_connection_returns_connection(self):

        self._initialize_database()

        connection = self._interface._get_connection()

        self.assertIsInstance(
            connection,
            sqlite3.Connection
        )

        connection.close()

    #
    # Schema
    #

    def test_create_table_creates_table(self):

        self._interface.create_table(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """,
            "users"
        )

        result = self._interface.run_query(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )

        self.assertEqual(
            "users",
            result[0][0]
        )

    def test_create_table_raises_on_invalid_sql(self):

        with self.assertRaises(SqliteInterfaceException):
            self._interface.create_table(
                "INVALID SQL",
                "users"
            )

    #
    # Queries
    #

    def test_insert_query_inserts_record(self):

        self._interface.create_table(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """,
            "users"
        )

        row_id = self._interface.insert_query(
            "INSERT INTO users(username) VALUES(?)",
            ("paul",)
        )

        self.assertEqual(
            1,
            row_id
        )

    def test_bulk_insert_query_inserts_records(self):

        self._interface.create_table(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """,
            "users"
        )

        result = self._interface.bulk_insert_query(
            "INSERT INTO users(username) VALUES(?)",
            [
                ("paul",),
                ("alice",)
            ]
        )

        self.assertTrue(result)

        rows = self._interface.run_query(
            "SELECT * FROM users"
        )

        self.assertEqual(
            2,
            len(rows)
        )

    def test_run_query_fetches_all_rows(self):

        self._interface.create_table(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """,
            "users"
        )

        self._interface.insert_query(
            "INSERT INTO users(username) VALUES(?)",
            ("paul",)
        )

        rows = self._interface.run_query(
            "SELECT * FROM users"
        )

        self.assertEqual(
            1,
            len(rows)
        )

    def test_run_query_fetch_one_returns_single_row(self):

        self._interface.create_table(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """,
            "users"
        )

        self._interface.insert_query(
            "INSERT INTO users(username) VALUES(?)",
            ("paul",)
        )

        row = self._interface.run_query(
            "SELECT * FROM users",
            fetch_one=True
        )

        self.assertEqual(
            "paul",
            row[1]
        )

    def test_run_query_commit_returns_rowcount(self):

        self._interface.create_table(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """,
            "users"
        )

        rowcount = self._interface.run_query(
            "INSERT INTO users(username) VALUES(?)",
            ("paul",),
            commit=True
        )

        self.assertEqual(
            1,
            rowcount
        )

    def test_run_query_returns_none_for_non_select(self):

        self._interface.create_table(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """,
            "users"
        )

        result = self._interface.run_query(
            "CREATE TABLE test(id INTEGER)"
        )

        self.assertIsNone(result)

    def test_run_query_raises_on_invalid_query(self):

        with self.assertRaises(SqliteInterfaceException):
            self._interface.run_query(
                "INVALID SQL"
            )

    #
    # Delete
    #

    def test_delete_query_removes_records(self):

        self._interface.create_table(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """,
            "users"
        )

        self._interface.insert_query(
            "INSERT INTO users(username) VALUES(?)",
            ("paul",)
        )

        self._interface.delete_query(
            "DELETE FROM users WHERE username=?",
            ("paul",)
        )

        rows = self._interface.run_query(
            "SELECT * FROM users"
        )

        self.assertEqual(
            0,
            len(rows)
        )

    #
    # Scripts
    #

    def test_run_script_executes_query(self):

        self._interface.run_script(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """)

        rows = self._interface.run_query("SELECT name FROM sqlite_master WHERE type='table'")

        self.assertEqual("users", rows[0][0])

    def test_run_script_raises_on_invalid_sql(self):

        with self.assertRaises(SqliteInterfaceException):
            self._interface.run_script("INVALID SQL")

    def test_insert_query_raises_on_invalid_query(self):

        with self.assertRaises(SqliteInterfaceException):
            self._interface.insert_query("INVALID SQL")

    def test_is_valid_database_returns_false_on_os_error(self):

        interface = SqliteInterface(
            self._logger,
            "Z:/this/path/does/not/exist/database.db"
        )

        self.assertFalse(
            interface.is_valid_database()
        )

    def test_run_query_raises_sqlite_interface_exception(self):

        self._initialize_database()

        with self.assertRaises(SqliteInterfaceException):
            self._interface.run_query(
                "SELECT * FROM table_that_does_not_exist"
            )

    def test_bulk_insert_query_raises_on_invalid_table(self):

        self._initialize_database()

        with self.assertRaises(SqliteInterfaceException):
            self._interface.bulk_insert_query(
                "INSERT INTO table_that_does_not_exist(name) VALUES(?)",
                [
                    ("paul",),
                    ("alice",)])

    def test_insert_query_raises_on_invalid_table(self):

        self._initialize_database()

        with self.assertRaises(SqliteInterfaceException):
            self._interface.insert_query(
                "INSERT INTO table_that_does_not_exist(name) VALUES(?)",
                ("paul",))

    def test_delete_query_raises_on_invalid_table(self):

        self._initialize_database()

        with self.assertRaises(SqliteInterfaceException):
            self._interface.delete_query(
                "DELETE FROM table_that_does_not_exist WHERE id=?",
                (1,))
