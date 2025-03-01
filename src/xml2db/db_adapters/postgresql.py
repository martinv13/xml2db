import logging
from typing import Any

from sqlalchemy import (
    Integer,
    Double,
    Boolean,
    BigInteger,
    SmallInteger,
    DateTime,
    String,
    LargeBinary,
)

logger = logging.getLogger(__name__)


class PostgreSQLAdapter:

    @classmethod
    def types_mapping(cls, temp: bool, col: "DataModelColumn") -> Any:
        """Defines the sqlalchemy type to use for given column properties in target tables

        Args:
            temp: are we targeting the temporary tables schema or the final tables?
            col: an object representing a column of a table for which we are determining the SQL type to define

        Returns:
            a sqlalchemy class representing the data type to be used
        """
        if col.occurs[1] != 1:
            return String(8000)
        if col.data_type in ["decimal", "float", "double"]:
            return Double
        if col.data_type == "dateTime":
            return DateTime(timezone=True)
        if col.data_type in [
            "integer",
            "int",
            "nonPositiveInteger",
            "nonNegativeInteger",
            "positiveInteger",
            "negativeInteger",
        ]:
            return Integer
        if col.data_type == "boolean":
            return Boolean
        if col.data_type in ["short", "byte"]:
            return SmallInteger
        if col.data_type == "long":
            return BigInteger
        if col.data_type == "date":
            return String(16)
        if col.data_type == "time":
            return String(18)
        if col.data_type in ["string", "NMTOKEN", "duration", "token"]:
            if col.max_length is None:
                return String(1000)
            min_length = 0 if col.min_length is None else col.min_length
            if min_length >= col.max_length - 1 and not col.allow_empty:
                return String(col.max_length)
            return String(col.max_length)
        if col.data_type == "binary":
            return LargeBinary(col.max_length)
        else:
            logger.warning(
                f"unknown type '{col.data_type}' for column '{col.name}', defaulting to VARCHAR(1000) "
                f"(this can be overridden by providing a field type in the configuration)"
            )
            return String(1000)
