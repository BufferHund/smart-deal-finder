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
                    CREATE TABLE IF NOT EXISTS loyalty_cards (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        store_name VARCHAR(255),
                        card_number VARCHAR(255),
                        card_format VARCHAR(50) DEFAULT 'BARCODE',
                        color VARCHAR(50) DEFAULT 'bg-gray-500',
                        image_path VARCHAR(255),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
                        product_name VARCHAR(500),
                        price DECIMAL(10, 2),
                        original_price VARCHAR(100),
                        unit VARCHAR(255),
                        store VARCHAR(100),
                        confidence FLOAT,
                        source VARCHAR(50),
                        category VARCHAR(50),
                        image_url VARCHAR(255),
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
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS receipts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        store_name VARCHAR(255),
                        total_amount DECIMAL(10, 2),
                        purchase_date DATE,
                        image_path VARCHAR(255),
                        items JSON,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS app_tokens (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        token VARCHAR(255) UNIQUE,
                        token_type VARCHAR(50) DEFAULT 'trial',
                        usage_count INT DEFAULT 0,
                        last_used_date DATE,
                        max_daily_limit INT DEFAULT 1000,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS ai_audit_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        feature VARCHAR(50),
                        model VARCHAR(50),
                        prompt_chars INT,
                        image_present BOOLEAN DEFAULT FALSE,
                        response_chars INT,
                        tokens_used INT DEFAULT 0,
                        cost_usd FLOAT DEFAULT 0.0,
                        latency_ms INT DEFAULT 0,
                        status VARCHAR(20),
                        error_msg TEXT,
                        raw_input MEDIUMTEXT,
                        raw_output MEDIUMTEXT
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS system_settings (
                        setting_key VARCHAR(50) PRIMARY KEY,
                        setting_value VARCHAR(255),
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                    """
                ]
                
                for table_sql in tables:
                    cursor.execute(table_sql)
                
                # Ensure default user exists
                cursor.execute("SELECT * FROM users WHERE unique_id = 'default_user'")
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO users (unique_id) VALUES ('default_user')")
                
                # Initialize trial token from environment variable (if set)
                trial_token = os.environ.get("TRIAL_API_KEY", "")
                if trial_token:
                    cursor.execute("SELECT * FROM app_tokens WHERE token = %s", (trial_token,))
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO app_tokens (token, token_type, max_daily_limit) VALUES (%s, 'trial', 1000)",
                            (trial_token,)
                        )
                    
                # Schema Migration (Quick Hack for Dev)
                # Check if card_format exists in loyalty_cards
                try:
                    cursor.execute("SELECT card_format FROM loyalty_cards LIMIT 1")
                except pymysql.Error:
                    # Column likely missing, add it
                    cursor.execute("ALTER TABLE loyalty_cards ADD COLUMN card_format VARCHAR(50) DEFAULT 'BARCODE'")
                
                # Expand deals columns if they are old size
                try:
                    cursor.execute("ALTER TABLE deals MODIFY COLUMN unit VARCHAR(255)")
                    cursor.execute("ALTER TABLE deals MODIFY COLUMN original_price VARCHAR(100)")
                    cursor.execute("ALTER TABLE deals MODIFY COLUMN product_name VARCHAR(500)")
                except pymysql.Error as e:
                    print(f"Migration Note (Deals): {e}")
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

    def execute_many(self, query, params_list):
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
        except pymysql.Error as err:
            print(f"Bulk Query Error: {err}")
            raise err
        finally:
            conn.close()

db = DatabaseManager()
