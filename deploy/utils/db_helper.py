"""
Database helper utilities
Handles database initialization and data loading
"""

import psycopg2
import csv
from pathlib import Path
from .logger import Logger

class DatabaseHelper:
    """Helper class for database operations"""
    
    def __init__(self, config):
        self.config = config
        self.logger = Logger()
        self.conn = None
    
    def connect(self, host='127.0.0.1', port=5432):
        """Connect to database via Cloud SQL Proxy"""
        try:
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                database=self.config['database_name'],
                user=self.config['credentials']['app_user'],
                password=self.config['credentials']['app_password']
            )
            self.logger.success("Connected to database")
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.logger.debug("Disconnected from database")
    
    def run_sql_scripts(self, scripts_dir):
        """Execute all SQL scripts in a directory"""
        scripts_path = Path(scripts_dir)
        if not scripts_path.exists():
            self.logger.warning(f"Scripts directory not found: {scripts_dir}")
            return False
        
        sql_files = sorted(scripts_path.glob("*.sql"))
        
        if not sql_files:
            self.logger.warning("No SQL files found")
            return True
        
        self.logger.info(f"Found {len(sql_files)} SQL script(s)")
        
        cursor = self.conn.cursor()
        
        for sql_file in sql_files:
            self.logger.info(f"Executing {sql_file.name}...")
            
            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                    
                    # Split by semicolon and execute each statement
                    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                    
                    for statement in statements:
                        cursor.execute(statement)
                
                self.logger.success(f"✓ {sql_file.name}")
            
            except Exception as e:
                self.logger.error(f"Failed to execute {sql_file.name}: {e}")
                cursor.close()
                return False
        
        self.conn.commit()
        cursor.close()
        self.logger.success("All SQL scripts executed successfully")
        return True
    
    def load_csv_data(self, csv_dir, tables):
        """Load CSV files into database tables"""
        csv_path = Path(csv_dir)
        if not csv_path.exists():
            self.logger.warning(f"CSV directory not found: {csv_dir}")
            return False
        
        cursor = self.conn.cursor()
        total_rows = 0
        
        for table_name in tables:
            csv_file = csv_path / f"{table_name}.csv"
            
            if not csv_file.exists():
                self.logger.warning(f"CSV file not found: {csv_file.name}, skipping...")
                continue
            
            self.logger.info(f"Loading {table_name}...")
            
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # First row = column names
                    
                    # Build INSERT query
                    columns = ','.join(header)
                    placeholders = ','.join(['%s'] * len(header))
                    
                    # Use ON CONFLICT DO NOTHING to skip duplicates
                    query = f"""
                        INSERT INTO {table_name} ({columns}) 
                        VALUES ({placeholders})
                        ON CONFLICT DO NOTHING
                    """
                    
                    # Insert all rows
                    rows_inserted = 0
                    for row in reader:
                        try:
                            cursor.execute(query, row)
                            rows_inserted += 1
                        except Exception as e:
                            self.logger.debug(f"  Skipped row in {table_name}: {e}")
                    
                    total_rows += rows_inserted
                    self.logger.success(f"✓ {table_name}: {rows_inserted} rows")
            
            except Exception as e:
                self.logger.error(f"Failed to load {table_name}: {e}")
                cursor.close()
                return False
        
        self.conn.commit()
        cursor.close()
        self.logger.success(f"Loaded {total_rows} total rows")
        return True
    
    def verify_tables(self):
        """Verify tables exist and show row counts"""
        cursor = self.conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            self.logger.warning("No tables found in database")
            return False
        
        self.logger.info(f"Found {len(tables)} table(s):")
        
        table_data = []
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            table_data.append([table_name, count])
        
        self.logger.table(table_data, ["Table", "Rows"])
        
        cursor.close()
        return True
    
    def test_connection(self):
        """Test database connection"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


def download_csv_from_bucket(bucket_name, remote_path, local_path):
    """Download CSV files from Cloud Storage"""
    import subprocess
    
    logger = Logger()
    logger.info(f"Downloading from gs://{bucket_name}/{remote_path}")
    
    try:
        subprocess.run(
            f"gsutil -m cp -r gs://{bucket_name}/{remote_path} {local_path}",
            shell=True,
            check=True
        )
        logger.success("Download complete")
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False
