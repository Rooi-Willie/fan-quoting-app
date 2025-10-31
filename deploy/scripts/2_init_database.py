#!/usr/bin/env python3
"""
Step 2: Initialize Cloud SQL Database
Creates database instance and loads initial data
"""

import sys
import yaml
import subprocess
import time
from pathlib import Path

# Add deploy directory to path for utils imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import Logger
from utils.gcp_helper import GCPHelper
from utils.db_helper import DatabaseHelper


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def upload_csv_files(config, gcp):
    """Upload CSV files to Cloud Storage"""
    logger = Logger()
    logger.info("Uploading CSV files to Cloud Storage...")
    
    bucket_name = config['data_storage']['bucket_name']
    # Make path relative to project root (parent of deploy folder)
    project_root = Path(__file__).parent.parent.parent
    csv_source = project_root / config['data_storage']['csv_source_path']
    
    # Create bucket
    gcp.create_storage_bucket(bucket_name)
    
    # Upload each CSV file
    csv_files = list(csv_source.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {csv_source}")
        return False
    
    logger.info(f"Found {len(csv_files)} CSV files")
    
    # Check if files already exist in bucket and skip if unchanged
    uploaded_count = 0
    skipped_count = 0
    
    for csv_file in csv_files:
        remote_path = f"csv_data/{csv_file.name}"
        
        # Check if file exists in bucket (simple check - could add MD5 comparison for accuracy)
        check_result = gcp.run_command(
            f"gsutil ls gs://{bucket_name}/{remote_path}",
            check=False
        )
        
        if check_result and check_result.strip():
            logger.debug(f"Skipping {csv_file.name} (already exists)")
            skipped_count += 1
        else:
            logger.debug(f"Uploading {csv_file.name}...")
            gcp.upload_to_bucket(
                str(csv_file),
                bucket_name,
                remote_path
            )
            uploaded_count += 1
    
    if uploaded_count > 0:
        logger.success(f"Uploaded {uploaded_count} file(s) to gs://{bucket_name}/csv_data/")
    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} file(s) (already exist)")
    
    return True
    return True


def start_cloud_sql_proxy(project_id, region, instance_name):
    """Start Cloud SQL Proxy in background"""
    logger = Logger()
    proxy_path = Path(__file__).parent.parent / "bin" / "cloud_sql_proxy.exe"
    
    # Download proxy if not exists
    if not proxy_path.exists():
        logger.info("Downloading Cloud SQL Proxy...")
        try:
            subprocess.run(
                f'powershell -Command "Invoke-WebRequest -Uri https://dl.google.com/cloudsql/cloud_sql_proxy_x64.exe -OutFile \\"{proxy_path}\\""',
                shell=True,
                check=True
            )
            logger.success("Cloud SQL Proxy downloaded")
        except Exception as e:
            logger.exit_with_error(f"Failed to download proxy: {e}")
    
    # Start proxy
    connection_name = f"{project_id}:{region}:{instance_name}"
    logger.info("Starting Cloud SQL Proxy...")
    logger.debug(f"Connection name: {connection_name}")
    
    try:
        # Start proxy with explicit port binding (using legacy v1 syntax)
        # The proxy will listen on localhost:5432
        process = subprocess.Popen(
            [str(proxy_path), "-instances", f"{connection_name}=tcp:5432"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for proxy to start and check for errors
        logger.info("Waiting for proxy to establish connection...")
        time.sleep(10)
        
        if process.poll() is not None:
            # Proxy exited, get error output
            stdout, stderr = process.communicate()
            logger.error(f"Proxy stdout: {stdout}")
            logger.error(f"Proxy stderr: {stderr}")
            logger.exit_with_error("Cloud SQL Proxy failed to start")
        
        logger.success(f"Cloud SQL Proxy running (PID: {process.pid})")
        return process
    
    except Exception as e:
        logger.exit_with_error(f"Failed to start proxy: {e}")


def stop_proxy(process):
    """Stop Cloud SQL Proxy"""
    if process:
        process.terminate()
        Logger().info("Cloud SQL Proxy stopped")


def main():
    logger = Logger()
    logger.header("DATABASE INITIALIZATION")
    
    # Load configuration
    config = load_config()
    
    project_id = config['gcp']['project_id']
    region = config['gcp']['region']
    db_config = config['database']
    instance_name = db_config['instance_name']
    
    # Initialize helpers
    gcp = GCPHelper(project_id, region)
    gcp.set_project()
    
    logger.section("DATABASE SETUP PLAN")
    logger.info("This script will:")
    logger.info("  1. Create Cloud SQL instance")
    logger.info("  2. Create database and user")
    logger.info("  3. Store credentials in Secret Manager")
    logger.info("  4. Upload CSV files to Cloud Storage")
    logger.info("  5. Initialize database schema")
    logger.info("  6. Load initial data")
    
    logger.warning(f"\nEstimated time: 10-15 minutes")
    logger.warning(f"Estimated cost: ~${25}/month")
    
    if not logger.confirm("\nProceed?", default=True):
        logger.warning("Cancelled")
        sys.exit(0)
    
    # Step 1: Create Cloud SQL instance
    logger.step(1, 6, f"Creating Cloud SQL instance: {instance_name}")
    
    if gcp.instance_exists(instance_name):
        logger.info("Instance already exists, skipping creation")
        # Ensure timezone is set for existing instances
        logger.info("Verifying timezone configuration...")
        gcp.set_database_timezone(instance_name)
    else:
        logger.info("This will take 5-10 minutes...")
        
        try:
            with logger.spinner("Creating instance"):
                gcp.create_sql_instance(instance_name, db_config)
            
            logger.success("Cloud SQL instance created with timezone set to Africa/Johannesburg")
        except Exception as e:
            logger.exit_with_error(f"Failed to create instance: {e}")
    
    # Step 2: Create database and user
    logger.step(2, 6, "Setting up database and user")
    
    db_name = db_config['database_name']
    db_user = db_config['credentials']['app_user']
    db_password = db_config['credentials']['app_password']
    
    # Create database
    if gcp.database_exists(instance_name, db_name):
        logger.info(f"Database '{db_name}' already exists")
    else:
        gcp.create_database(instance_name, db_name)
        logger.success(f"Database '{db_name}' created")
    
    # Create user
    if gcp.user_exists(instance_name, db_user):
        logger.info(f"User '{db_user}' already exists, updating password")
        gcp.update_user_password(instance_name, db_user, db_password)
    else:
        gcp.create_sql_user(instance_name, db_user, db_password)
        logger.success(f"User '{db_user}' created")
    
    # Step 3: Store credentials in Secret Manager
    logger.step(3, 6, "Storing credentials in Secret Manager")
    
    gcp.create_secret("db-password", db_password)
    gcp.create_secret("api-key", config['api']['api_key'])
    
    # Grant access to compute service account (used by Cloud Run)
    # Get project number for the default compute service account
    project_number = gcp.run_command(
        f"gcloud projects describe {project_id} --format=value(projectNumber)",
        check=False
    )
    if project_number:
        compute_sa = f"{project_number}-compute@developer.gserviceaccount.com"
        logger.info(f"Granting access to: {compute_sa}")
        gcp.grant_secret_access("db-password", compute_sa)
        gcp.grant_secret_access("api-key", compute_sa)
    else:
        logger.warning("Could not get project number, skipping service account permissions")
    
    logger.success("Credentials stored securely")
    
    # Step 4: Upload CSV files
    logger.step(4, 6, "Uploading CSV data to Cloud Storage")
    upload_csv_files(config, gcp)
    
    # Step 5 & 6: Initialize database
    logger.step(5, 6, "Initializing database schema and data")
    
    proxy_process = None
    try:
        # Start Cloud SQL Proxy
        proxy_process = start_cloud_sql_proxy(project_id, region, instance_name)
        
        # Connect to database
        db_helper = DatabaseHelper(db_config)
        if not db_helper.connect():
            logger.exit_with_error("Failed to connect to database")
        
        # Run init scripts - use absolute path, but skip 02-load-data.sql
        project_root = Path(__file__).parent.parent.parent
        scripts_dir = project_root / "database" / "init-scripts"
        logger.info("Running SQL initialization scripts...")
        # Only run schema creation (01-schema.sql), skip 02-load-data.sql
        # because COPY FROM requires superuser privileges which Cloud SQL doesn't provide
        if not db_helper.run_sql_scripts(str(scripts_dir), skip_files=['02-load-data.sql']):
            logger.exit_with_error("Failed to run SQL scripts")
        
        # Load CSV data - use absolute path
        # This uses Python's psycopg2 which doesn't require superuser privileges
        logger.info("Loading CSV data from local files...")
        csv_dir = project_root / config['data_storage']['csv_source_path']
        tables = config['data_storage']['csv_tables']
        
        if not db_helper.load_csv_data(str(csv_dir), tables):
            logger.exit_with_error("Failed to load CSV data")
        
        # Verify
        logger.info("\nVerifying database...")
        db_helper.verify_tables()
        
        db_helper.disconnect()
        logger.success("Database initialized successfully")
    
    except Exception as e:
        logger.exit_with_error(f"Database initialization failed: {e}")
    
    finally:
        stop_proxy(proxy_process)
    
    # Summary
    logger.section("DATABASE READY!")
    
    connection_string = f"{project_id}:{region}:{instance_name}"
    
    logger.summary({
        "Instance": instance_name,
        "Database": db_name,
        "Connection": connection_string,
        "CSV Files": "Uploaded to Cloud Storage",
        "Schema": "Initialized",
        "Data": "Loaded"
    })
    
    logger.info("\nNext Steps:")
    logger.info("  1. Run: python deploy/3_deploy_api.py")
    logger.success("\nDatabase ready! 🎉")


if __name__ == "__main__":
    main()
