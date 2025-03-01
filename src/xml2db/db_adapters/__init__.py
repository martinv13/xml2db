from .duckdb import DuckDBAdapter
from .mssql import MSSQLAdapter
from .mysql import MySQLAdapter
from .postgresql import PostgreSQLAdapter

adapters = {
    "duckdb": DuckDBAdapter,
    "mssql": MSSQLAdapter,
    "mysql": MySQLAdapter,
    "postgresql": PostgreSQLAdapter,
}
