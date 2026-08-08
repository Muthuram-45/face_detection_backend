import psycopg2
import sys

URL = "postgresql://postgres.qpwqyvtozuxpgbkkobnp:muthuram921@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"

try:
    print("Connecting...")
    conn = psycopg2.connect(URL, connect_timeout=5)
    print("Success!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
