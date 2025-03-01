import logging

from .postgresql import PostgreSQLAdapter

logger = logging.getLogger(__name__)


class DuckDBAdapter(PostgreSQLAdapter):
    pass
