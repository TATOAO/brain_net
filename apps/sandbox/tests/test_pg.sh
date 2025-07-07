### Test sandbox with database PG

pg_code="import psycopg2\nconn = psycopg2.connect(host=\"localhost\", database=\"postgres\", user=\"postgres\", password=\"postgres\")\ncursor = conn.cursor()\ncursor.execute(\"SELECT 1\")\nresult = cursor.fetchone()\nprint(result)"

curl -X POST http://localhost:8002/execute -H "Content-Type: application/json" -d '{"code": "import psycopg2\nconn = psycopg2.connect(host=\"localhost\", database=\"postgres\", user=\"postgres\", password=\"postgres\")\ncursor = conn.cursor()\ncursor.execute(\"SELECT 1\")\nresult = cursor.fetchone()\nprint(result)"}'