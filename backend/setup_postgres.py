"""
Setup PostgreSQL database and user for Oxidane
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL with default postgres user
print("Connecting to PostgreSQL...")
try:
    # Try to connect to default postgres database
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='1Halloween.',
        host='localhost',
        port='5432'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    print("✅ Connected to PostgreSQL")
    
    # Update or create user
    print("\nSetting up user 'oxidane'...")
    try:
        # Try to alter password if user exists
        cur.execute("ALTER USER oxidane WITH PASSWORD '1Halloween.';")
        print("  - Updated password for existing user 'oxidane'")
    except Exception as e:
        # If user doesn't exist, create it
        try:
            cur.execute("CREATE USER oxidane WITH PASSWORD '1Halloween.';")
            print("  - Created user 'oxidane'")
        except Exception as e2:
            print(f"  - Error: {e2}")
    
    # Create database if it doesn't exist
    print("\nSetting up database 'oxidane'...")
    try:
        cur.execute("CREATE DATABASE oxidane OWNER oxidane;")
        print("  - Created database 'oxidane'")
    except Exception as e:
        if "already exists" in str(e):
            print("  - Database 'oxidane' already exists (OK)")
        else:
            print(f"  - Error: {e}")
    
    # Grant privileges
    cur.execute("GRANT ALL PRIVILEGES ON DATABASE oxidane TO oxidane;")
    print("  - Granted all privileges")
    
    cur.close()
    conn.close()
    
    # Test connection with new user
    print("\nTesting connection with new credentials...")
    test_conn = psycopg2.connect(
        dbname='oxidane',
        user='oxidane',
        password='1Halloween.',
        host='localhost',
        port='5432'
    )
    test_cur = test_conn.cursor()
    test_cur.execute("SELECT version();")
    version = test_cur.fetchone()[0]
    print(f"✅ Connection successful!")
    print(f"PostgreSQL version: {version[:50]}...")
    test_cur.close()
    test_conn.close()
    
    print("\n" + "="*60)
    print("✅ PostgreSQL setup complete!")
    print("="*60)
    print("\nDatabase: oxidane")
    print("User: oxidane")
    print("Password: 1Halloween.")
    print("Host: localhost")
    print("Port: 5432")
    
except psycopg2.OperationalError as e:
    print(f"\n❌ Error: {e}")
    print("\nPlease ensure:")
    print("1. PostgreSQL is running")
    print("2. You can connect to PostgreSQL (check pg_hba.conf)")
    print("3. The postgres superuser is accessible")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
