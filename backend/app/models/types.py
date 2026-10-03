import json
from sqlalchemy import TypeDecorator, Text
from backend.app.core.config import settings

try:
    from pgvector.sqlalchemy import Vector as PgVector
    
    class VectorType(TypeDecorator):
        """Vector type that gracefully falls back to JSON Text in SQLite for testing."""
        impl = Text
        cache_ok = True

        def load_dialect_impl(self, dialect):
            if dialect.name == "postgresql":
                return dialect.type_descriptor(PgVector(settings.EMBEDDING_DIMENSION))
            return dialect.type_descriptor(Text())

        def process_bind_param(self, value, dialect):
            if value is None:
                return None
            if dialect.name == "postgresql":
                return value
            if isinstance(value, (list, tuple)):
                return json.dumps(list(value))
            return str(value)

        def process_result_value(self, value, dialect):
            if value is None:
                return None
            if dialect.name == "postgresql":
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except Exception:
                    return value
            return value

except ImportError:
    class VectorType(TypeDecorator):
        impl = Text
        cache_ok = True
