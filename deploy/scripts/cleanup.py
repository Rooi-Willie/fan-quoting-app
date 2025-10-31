#!/usr/bin/env python3
"""
Cleanup Script - Delete All Cloud Resources
⚠️  WARNING: This is DESTRUCTIVE and IRREVERSIBLE!
"""

import sys
import yaml
from pathlib import Path

# Add deploy directory to path for utils imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import Logger
from utils.gcp_helper import GCPHelper


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    logger = Logger()
    logger.header("⚠️  DESTRUCTIVE CLEANUP WARNING ⚠️")
    
    config = load_config()
    
    project_id = config['gcp']['project_id']
    region = config['gcp']['region']
    service_name = config['api']['service_name']
    instance_name = config['database']['instance_name']
    bucket_name = config['data_storage']['bucket_name']
    
    logger.section("RESOURCES TO DELETE")
    logger.error("This will PERMANENTLY DELETE:")
    logger.info(f"  - Cloud Run service: {service_name}")
    logger.info(f"  - Cloud SQL instance: {instance_name}")
    logger.info(f"  - Storage bucket: {bucket_name}")
    logger.info("  - All secrets in Secret Manager")
    logger.info("  - ALL DATA IN THE DATABASE")
    
    logger.warning("\n⚠️  THIS CANNOT BE UNDONE!")
    logger.warning("⚠️  ALL DATA WILL BE LOST!")
    
    if not logger.confirm("\nAre you absolutely sure?", default=False):
        logger.info("Cancelled - no resources deleted")
        sys.exit(0)
    
    # Double confirmation
    confirmation = logger.prompt("\nType 'DELETE' to confirm", default="")
    if confirmation != "DELETE":
        logger.info("Cancelled - confirmation did not match")
        sys.exit(0)
    
    # Initialize GCP helper
    gcp = GCPHelper(project_id, region)
    gcp.set_project()
    
    logger.section("DELETING RESOURCES")
    
    # Delete Cloud Run service
    logger.step(1, 4, "Deleting Cloud Run service...")
    try:
        if gcp.service_exists(service_name):
            gcp.delete_service(service_name)
            logger.success("Cloud Run service deleted")
        else:
            logger.info("Cloud Run service not found")
    except Exception as e:
        logger.warning(f"Error deleting service: {e}")
    
    # Delete Cloud SQL instance
    logger.step(2, 4, "Deleting Cloud SQL instance (2-3 minutes)...")
    try:
        if gcp.instance_exists(instance_name):
            with logger.spinner("Deleting database"):
                gcp.delete_sql_instance(instance_name)
            logger.success("Cloud SQL instance deleted")
        else:
            logger.info("Cloud SQL instance not found")
    except Exception as e:
        logger.warning(f"Error deleting instance: {e}")
    
    # Delete Storage bucket
    logger.step(3, 4, "Deleting Storage bucket...")
    try:
        gcp.run_command(f"gsutil -m rm -r gs://{bucket_name}", check=False)
        logger.success("Storage bucket deleted")
    except Exception as e:
        logger.warning(f"Error deleting bucket: {e}")
    
    # Delete secrets
    logger.step(4, 4, "Deleting secrets...")
    try:
        gcp.delete_secret("db-password")
        gcp.delete_secret("api-key")
        logger.success("Secrets deleted")
    except Exception as e:
        logger.warning(f"Error deleting secrets: {e}")
    
    # Summary
    logger.section("CLEANUP COMPLETE")
    logger.success("All resources deleted")
    
    logger.info("\nTo redeploy:")
    logger.info("  1. python deploy/2_init_database.py")
    logger.info("  2. python deploy/3_deploy_api.py")
    logger.info("  3. python deploy/4_deploy_ui.py")
    
    logger.warning("\nNote: The GCP project itself was not deleted")
    logger.info("To delete the entire project:")
    logger.info(f"  gcloud projects delete {project_id}")


if __name__ == "__main__":
    main()
