from db import db

def run_migration():
    print("Migrating deals table...")
    conn = db._get_conn()
    try:
        with conn.cursor() as cursor:
            # Add category
            try:
                cursor.execute("SELECT category FROM deals LIMIT 1")
                print("Column 'category' exists.")
            except:
                print("Adding 'category' column...")
                cursor.execute("ALTER TABLE deals ADD COLUMN category VARCHAR(50)")
            
            # Add image_url
            try:
                cursor.execute("SELECT image_url FROM deals LIMIT 1")
                print("Column 'image_url' exists.")
            except:
                print("Adding 'image_url' column...")
                cursor.execute("ALTER TABLE deals ADD COLUMN image_url VARCHAR(255)")
                
        print("Migration complete.")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
