import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "bankdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=5432
    )

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Bank API is running",
        "environment": os.getenv("ENV", "production"),
        "status": "OK"
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/accounts', methods=['GET'])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM accounts;")
        accounts = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(accounts), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)