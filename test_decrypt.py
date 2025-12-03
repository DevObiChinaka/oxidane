from cryptography.fernet import Fernet
import psycopg2

# Get encrypted token from database
conn = psycopg2.connect('postgresql://oxidane:Oxidane25@localhost:5432/oxidane_prod')
cur = conn.cursor()
cur.execute('SELECT bot_token FROM subscriptions_telegramconfiguration LIMIT 1')
encrypted_token = cur.fetchone()[0]
cur.close()
conn.close()

print('Encrypted token (first 30):', encrypted_token[:30])

# Test with hardcoded key from settings.py
print('\n1. Testing with HARDCODED key from settings.py...')
key1 = b'4ji0ZN6vG1VLvQR5cxb6hCPRzlbHwuVG-Q1NiTrq2c8='
f1 = Fernet(key1)
try:
    decrypted1 = f1.decrypt(encrypted_token.encode()).decode()
    print('   SUCCESS! Decrypted with hardcoded key')
    print('   Decrypted (first 30):', decrypted1[:30])
    print('   Contains colon:', ':' in decrypted1)
    if ':' in decrypted1:
        print('   Format is VALID!')
except Exception as e:
    print('   FAILED:', str(e)[:50])

# Test with .env key
print('\n2. Testing with .env key...')
key2 = b'hLwK0race8TsEQFV8WySAOX7aWvCOqMgl8Nw5TopAFE='
f2 = Fernet(key2)
try:
    decrypted2 = f2.decrypt(encrypted_token.encode()).decode()
    print('   SUCCESS! Decrypted with .env key')
    print('   Decrypted (first 30):', decrypted2[:30])
except Exception as e:
    print('   FAILED:', str(e)[:50])
