#!/usr/bin/env python3
"""Clear all data from the database and reset schema."""

import os
import subprocess
import glob
from sqlalchemy import create_engine, MetaData, text
from app.core.config import Settings

def clear_database(recreate_schema=True, clear_templates=True):
    """
    Drop all tables and optionally recreate schema.

    Args:
        recreate_schema: If True, run migrations to recreate tables
        clear_templates: If True, remove all invoice2data templates
    """
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)

    # Drop all tables
    print("Dropping all tables...")
    metadata = MetaData()
    metadata.reflect(bind=engine)
    table_count = len(metadata.tables)
    metadata.drop_all(bind=engine)
    print(f"✅ Dropped {table_count} tables")

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

    # Clear invoice2data templates if requested
    if clear_templates:
        templates_dir = "app/templates"
        if os.path.exists(templates_dir):
            templates = glob.glob(f"{templates_dir}/*.yml")
            for template in templates:
                os.remove(template)
            print(f"✅ Cleared {len(templates)} invoice templates")

    # Recreate schema using Alembic migrations
    if recreate_schema:
        print("\nRecreating database schema...")
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ Database schema recreated successfully!")
            print("\n✨ Database is ready to use!")
        except subprocess.CalledProcessError as e:
            print("❌ Failed to run migrations:")
            print(e.stderr)
            print("\nPlease run manually:")
            print("  alembic upgrade head")
    else:
        print("\nDatabase is now empty. Run migrations to recreate schema:")
        print("  alembic upgrade head")

if __name__ == "__main__":
    import sys

    # Parse command line arguments
    recreate = "--no-recreate" not in sys.argv
    templates = "--keep-templates" not in sys.argv

    print("Invoice Intelligence - Database Reset")
    print("=" * 50)
    print(f"Recreate schema: {recreate}")
    print(f"Clear templates: {templates}")
    print("=" * 50)
    print()

    clear_database(recreate_schema=recreate, clear_templates=templates)
