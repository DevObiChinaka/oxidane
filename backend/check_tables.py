"""
Check which subscription tables exist in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname='public' 
    AND tablename LIKE 'subscriptions_%' 
    ORDER BY tablename
""")

tables = [row[0] for row in cursor.fetchall()]
print("Existing subscription tables:")
print("-" * 50)
for table in tables:
    print(f"  - {table}")
print(f"\nTotal: {len(tables)} tables")
