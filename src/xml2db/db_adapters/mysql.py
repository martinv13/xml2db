import logging
from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects import mysql

from .postgresql import PostgreSQLAdapter

logger = logging.getLogger(__name__)


class MySQLAdapter(PostgreSQLAdapter):

    @classmethod
    def types_mapping(cls, temp: bool, col: "DataModelColumn") -> Any:
        """Defines the MySQL/sqlalchemy type to use for given column properties in target tables

        Args:
            temp: are we targeting the temporary tables schema or the final tables?
            col: an object representing a column of a table for which we are determining the SQL type to define

        Returns:
            a sqlalchemy class representing the data type to be used
        """
        if col.occurs[1] != 1:
            return String(4000)
        if col.data_type in ["string", "NMTOKEN", "duration", "token"]:
            if col.max_length is None:
                return String(255)
        if col.data_type == "binary":
            if col.max_length == col.min_length:
                return mysql.BINARY(col.max_length)
            return mysql.VARBINARY(col.max_length)
        return super().types_mapping(temp, col)
