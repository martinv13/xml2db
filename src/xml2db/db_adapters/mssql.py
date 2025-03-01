import logging
from typing import Any

from sqlalchemy.dialects import mssql

from .postgresql import PostgreSQLAdapter

logger = logging.getLogger(__name__)


class MSSQLAdapter(PostgreSQLAdapter):

    @classmethod
    def types_mapping(cls, temp: bool, col: "DataModelColumn") -> Any:
        """Defines the MSSQL type to use for given column properties in target tables

        Args:
            temp: are we targeting the temporary tables schema or the final tables?
            col: an object representing a column of a table for which we are determining the SQL type to define

        Returns:
            a sqlalchemy class representing the data type to be used
        """
        if col.occurs[1] != 1:
            return mssql.VARCHAR(8000)
        if col.data_type == "dateTime":
            # using the DATETIMEOFFSET directly in the temporary table caused issues when inserting data in the target
            # table with INSERT INTO SELECT converts datetime VARCHAR to DATETIMEOFFSET without errors
            return mssql.VARCHAR(100) if temp else mssql.DATETIMEOFFSET
        if col.data_type == "date":
            return mssql.VARCHAR(16)
        if col.data_type == "time":
            return mssql.VARCHAR(18)
        if col.data_type in ["string", "NMTOKEN", "duration", "token"]:
            if col.max_length is None:
                return mssql.VARCHAR(1000)
            min_length = 0 if col.min_length is None else col.min_length
            if min_length >= col.max_length - 1 and not col.allow_empty:
                return mssql.CHAR(col.max_length)
            return mssql.VARCHAR(col.max_length)
        if col.data_type == "binary":
            if col.max_length == col.min_length:
                return mssql.BINARY(col.max_length)
            return mssql.VARBINARY(col.max_length)
        return super().types_mapping(temp, col)
