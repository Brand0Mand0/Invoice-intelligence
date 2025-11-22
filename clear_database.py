#!/usr/bin/env python3
"""Clear all data from the database."""

from sqlalchemy import create_engine, MetaData, text
from app.core.config import Settings

def clear_database():
    """Drop all tables and recreate schema."""
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)

    # Drop all tables
    print("Dropping all tables...")
    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(bind=engine)
    print(f"✅ Dropped {len(metadata.tables)} tables")

    # Verify tables are gone
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ))
        remaining_tables = [row[0] for row in result]
        if remaining_tables:
            print(f"⚠️  Remaining tables: {remaining_tables}")
        else:
            print("✅ All tables cleared!")

    print("\nDatabase is now empty. Run migrations to recreate schema:")
    print("  alembic upgrade head")

if __name__ == "__main__":
    clear_database()
