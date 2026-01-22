import pymysql
import pymysql.cursors
import os
import time
import json

class DatabaseManager:
    def __init__(self):
        # We won't hold a persistent connection anymore to avoid threading issues
        # Just init DB structure on startup
        self._init_db()

    def _get_conn(self):
        # Create a fresh connection for every operation
        # This is less efficient than pooling but 100% thread-safe and crash-proof for this scale
        try:
            return pymysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", "root"),
                database=os.getenv("DB_NAME", "smartdeal"),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
        except pymysql.Error as err:
            print(f"DB Connection Error: {err}")
            raise err

    def _init_db(self):
        # Create Tables
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                tables = [
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        unique_id VARCHAR(255) UNIQUE DEFAULT 'default_user',
                        api_key VARCHAR(255),
                        settings JSON
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS uploads (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        filename VARCHAR(255),
                        file_hash VARCHAR(64) UNIQUE,
                        file_path VARCHAR(255),
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        deal_count INT
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS deals (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        upload_id INT,
                        product_name VARCHAR(255),
                        price DECIMAL(10, 2),
                        original_price VARCHAR(50),
                        unit VARCHAR(50),
                        store VARCHAR(100),
                        confidence FLOAT,
                        source VARCHAR(50),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        valid_until DATETIME,
                        FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS shopping_list (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        item VARCHAR(255) UNIQUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS watchlist (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        item VARCHAR(255) UNIQUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                ]
                
                for table_sql in tables:
                    cursor.execute(table_sql)
                
                # Ensure default user exists
                cursor.execute("SELECT * FROM users WHERE unique_id = 'default_user'")
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO users (unique_id) VALUES ('default_user')")
        finally:
            conn.close()

    def execute_query(self, query, params=None):
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if query.strip().upper().startswith(("SELECT", "SHOW")):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.lastrowid
        except pymysql.Error as err:
            print(f"Query Error: {err}")
            raise err
        finally:
            conn.close()

db = DatabaseManager()
