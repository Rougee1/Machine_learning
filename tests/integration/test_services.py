import pytest
import requests
import psycopg2
import os
import time

def test_postgres_connection():
    """Test que PostgreSQL est accessible"""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="streamflow",
        password="streamflow",
        database="streamflow"
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    assert version is not None
    cur.close()
    conn.close()

def test_mlflow_health():
    """Test que MLflow est accessible"""
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            assert response.status_code == 200
            return
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                time.sleep(3)
            else:
                raise
