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
    
    def run_sql_scripts(self, scripts_dir, skip_files=None):
        """Execute all SQL scripts in a directory"""
        scripts_path = Path(scripts_dir)
        if not scripts_path.exists():
            self.logger.warning(f"Scripts directory not found: {scripts_dir}")
            return False
        
        skip_files = skip_files or []
        sql_files = sorted(scripts_path.glob("*.sql"))
        
        # Filter out skipped files
        sql_files = [f for f in sql_files if f.name not in skip_files]
        
        if not sql_files:
            self.logger.warning("No SQL files found")
            return True
        
        if skip_files:
            self.logger.info(f"Skipping: {', '.join(skip_files)}")
        
        self.logger.info(f"Found {len(sql_files)} SQL script(s) to execute")
        
        cursor = self.conn.cursor()
        
        for sql_file in sql_files:
            self.logger.info(f"Executing {sql_file.name}...")
            
            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                    
                    # Split by semicolon and execute each statement
                    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                    
                    for statement in statements:
                        try:
                            cursor.execute(statement)
                            # Commit after each statement to avoid transaction rollback issues
                            self.conn.commit()
                        except Exception as stmt_error:
                            # Rollback the failed transaction
                            self.conn.rollback()
                            
                            # Ignore "already exists" errors to make script idempotent
                            error_msg = str(stmt_error).lower()
                            if 'already exists' in error_msg or 'duplicate' in error_msg:
                                self.logger.debug(f"  Skipping: {stmt_error}")
                            else:
                                # Re-raise other errors
                                raise
                
                self.logger.success(f"✓ {sql_file.name}")
            
            except Exception as e:
                self.logger.error(f"Failed to execute {sql_file.name}: {e}")
                self.conn.rollback()
                cursor.close()
                return False
        
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
        
        # Define the order and special handling for tables
        # Some tables have dependencies and need to be loaded in order
        
        try:
            # 1. Load simple tables first (no dependencies)
            simple_tables = ['materials', 'labour_rates', 'global_settings']
            for table_name in simple_tables:
                if table_name in tables:
                    rows = self._load_simple_csv(cursor, csv_path, table_name)
                    if rows is not None:
                        total_rows += rows
            
            # 2. Handle motor data with special workflow
            if 'motors_master' in tables:
                rows = self._load_motor_data(cursor, csv_path)
                if rows is not None:
                    total_rows += rows
            
            # 3. Load motor supplier discounts
            if 'motor_supplier_discounts' in tables:
                rows = self._load_simple_csv(cursor, csv_path, 'motor_supplier_discounts')
                if rows is not None:
                    total_rows += rows
            
            # 4. Load fan configurations
            if 'fan_configurations' in tables:
                rows = self._load_simple_csv(cursor, csv_path, 'fan_configurations')
                if rows is not None:
                    total_rows += rows
            
            # 5. Load components
            if 'components' in tables:
                rows = self._load_simple_csv(cursor, csv_path, 'components')
                if rows is not None:
                    total_rows += rows
            
            # 6. Load component parameters (depends on components)
            if 'component_parameters' in tables:
                rows = self._load_simple_csv(cursor, csv_path, 'component_parameters')
                if rows is not None:
                    total_rows += rows
            
            # 7. Load fan component parameters (depends on fan_configurations and components)
            if 'fan_component_parameters' in tables:
                rows = self._load_simple_csv(cursor, csv_path, 'fan_component_parameters')
                if rows is not None:
                    total_rows += rows
            
            # 8. Load users
            if 'users' in tables:
                rows = self._load_simple_csv(cursor, csv_path, 'users')
                if rows is not None:
                    total_rows += rows
            
            self.conn.commit()
            cursor.close()
            self.logger.success(f"All CSV data loaded successfully ({total_rows} total rows)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV data: {e}")
            self.conn.rollback()
            cursor.close()
            return False
    
    def _load_simple_csv(self, cursor, csv_path, table_name):
        """Load a simple CSV file into a table using COPY FROM STDIN"""
        csv_file = csv_path / f"{table_name}.csv"
        
        if not csv_file.exists():
            self.logger.warning(f"CSV file not found: {csv_file.name}, skipping...")
            return None
        
        self.logger.info(f"Loading {table_name}...")
        
        try:
            # Read the header to get column names from CSV
            with open(csv_file, 'r', encoding='utf-8') as f:
                header_line = f.readline().strip()
                columns = header_line.split(',')
            
            # Create column list for COPY command
            column_list = ', '.join(columns)
            
            # Reopen file and skip header, then copy data
            with open(csv_file, 'r', encoding='utf-8') as f:
                next(f)  # Skip header row
                
                # Use COPY FROM STDIN with specific columns
                cursor.copy_expert(
                    f"COPY {table_name} ({column_list}) FROM STDIN WITH (FORMAT CSV, NULL '')",
                    f
                )
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            self.logger.success(f"✓ {table_name}: {count} rows")
            return count
            
        except Exception as e:
            self.logger.error(f"Failed to load {table_name}: {e}")
            raise
    
    def _load_motor_data(self, cursor, csv_path):
        """
        Load motor data with special workflow:
        1. Load into motors_staging
        2. Extract unique motors into motors table
        3. Extract prices into motor_prices table
        4. Drop staging table
        """
        csv_file = csv_path / "motors_master.csv"
        
        if not csv_file.exists():
            self.logger.warning("motors_master.csv not found, skipping motor data...")
            return None
        
        self.logger.info("Loading motor data (multi-step process)...")
        
        try:
            # Step 1: Load into staging table
            self.logger.debug("  Step 1/4: Loading into motors_staging...")
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Skip header
                next(f)
                cursor.copy_expert(
                    "COPY motors_staging FROM STDIN WITH (FORMAT CSV, NULL '')",
                    f
                )
            
            cursor.execute("SELECT COUNT(*) FROM motors_staging")
            staging_count = cursor.fetchone()[0]
            self.logger.debug(f"  Loaded {staging_count} rows into staging")
            
            # Step 2: Insert unique motors
            self.logger.debug("  Step 2/4: Extracting unique motors...")
            cursor.execute("""
                INSERT INTO motors (
                    supplier_name, product_range, part_number, poles, 
                    rated_output, rated_output_unit, speed, speed_unit, 
                    frame_size, shaft_diameter, shaft_diameter_unit
                )
                SELECT DISTINCT ON (supplier_name, product_range, poles, rated_output, speed, frame_size)
                    supplier_name, product_range, part_number, poles, 
                    rated_output, 'kW', speed, 'RPM', 
                    frame_size, shaft_diameter, 'mm'
                FROM motors_staging
                ON CONFLICT DO NOTHING
            """)
            motors_count = cursor.rowcount
            self.logger.debug(f"  Inserted {motors_count} unique motors")
            
            # Step 3: Insert motor prices
            self.logger.debug("  Step 3/4: Inserting motor prices...")
            cursor.execute("""
                INSERT INTO motor_prices (motor_id, date_effective, foot_price, flange_price, currency)
                SELECT 
                    m.id, s.date_effective, s.foot_price, s.flange_price, s.currency
                FROM motors_staging s
                JOIN motors m ON 
                    s.supplier_name = m.supplier_name AND
                    s.product_range = m.product_range AND
                    s.poles = m.poles AND
                    s.rated_output = m.rated_output AND
                    s.speed = m.speed AND
                    (s.frame_size = m.frame_size OR (s.frame_size IS NULL AND m.frame_size IS NULL))
                ON CONFLICT DO NOTHING
            """)
            prices_count = cursor.rowcount
            self.logger.debug(f"  Inserted {prices_count} price records")
            
            # Step 4: Drop staging table
            self.logger.debug("  Step 4/4: Cleaning up staging table...")
            cursor.execute("DROP TABLE motors_staging")
            
            self.logger.success(f"✓ motors: {motors_count} motors, {prices_count} prices")
            return motors_count + prices_count
            
        except Exception as e:
            self.logger.error(f"Failed to load motor data: {e}")
            raise
    
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
