#!/usr/bin/env python3
"""
Step 5: Monitor Deployment
View logs and check service status
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from utils.logger import Logger
from utils.gcp_helper import GCPHelper


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    logger = Logger()
    logger.header("DEPLOYMENT MONITORING")
    
    config = load_config()
    
    project_id = config['gcp']['project_id']
    region = config['gcp']['region']
    service_name = config['api']['service_name']
    instance_name = config['database']['instance_name']
    
    gcp = GCPHelper(project_id, region)
    gcp.set_project()
    
    while True:
        logger.section("SERVICE STATUS")
        
        # API Status
        logger.info("📦 Cloud Run API")
        if gcp.service_exists(service_name):
            api_url = gcp.get_service_url(service_name)
            logger.success(f"  Status: Running")
            logger.info(f"  URL: {api_url}")
            
            # Test endpoint
            try:
                import requests
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    logger.success("  Health: OK")
                else:
                    logger.warning(f"  Health: Status {response.status_code}")
            except:
                logger.error("  Health: Unreachable")
        else:
            logger.warning("  Status: Not deployed")
        
        # Database Status
        logger.info("\n💾 Cloud SQL Database")
        if gcp.instance_exists(instance_name):
            db_status = gcp.get_instance_status(instance_name)
            if db_status == "RUNNABLE":
                logger.success(f"  Status: {db_status}")
            else:
                logger.warning(f"  Status: {db_status}")
        else:
            logger.warning("  Status: Not created")
        
        # Cost Estimate
        logger.info("\n💰 Estimated Monthly Cost")
        if db_status == "RUNNABLE":
            logger.info("  ~$25-30 (services running)")
        else:
            logger.info("  ~$10-15 (database stopped)")
        
        # Menu
        logger.info("\n" + "="*60)
        logger.info("OPTIONS:")
        logger.info("  1. View API logs (last 50 lines)")
        logger.info("  2. View API errors only")
        logger.info("  3. View database operations")
        logger.info("  4. Refresh status")
        logger.info("  5. Test API endpoints")
        logger.info("  6. Exit")
        
        choice = logger.prompt("\nSelect option [1-6]", default="4")
        
        if choice == "1":
            logger.info("\nFetching API logs...")
            gcp.run_command(
                f"gcloud logs read 'resource.type=cloud_run_revision AND resource.labels.service_name={service_name}' --limit=50",
                capture_output=False
            )
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            logger.info("\nFetching errors...")
            gcp.run_command(
                f"gcloud logs read 'resource.type=cloud_run_revision AND resource.labels.service_name={service_name} AND severity>=ERROR' --limit=50",
                capture_output=False
            )
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            logger.info("\nFetching database operations...")
            gcp.run_command(
                f"gcloud sql operations list --instance={instance_name} --limit=10",
                capture_output=False
            )
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            continue
        
        elif choice == "5":
            if gcp.service_exists(service_name):
                logger.info("\nTesting endpoints...")
                api_url = gcp.get_service_url(service_name)
                
                import requests
                endpoints = ["/", "/health", "/api/test-db"]
                
                for endpoint in endpoints:
                    try:
                        resp = requests.get(f"{api_url}{endpoint}", timeout=5)
                        logger.success(f"  {endpoint}: {resp.status_code}")
                    except Exception as e:
                        logger.error(f"  {endpoint}: {e}")
                
                input("\nPress Enter to continue...")
            else:
                logger.warning("API not deployed")
                input("\nPress Enter to continue...")
        
        elif choice == "6":
            logger.info("Goodbye!")
            break
        
        else:
            logger.warning("Invalid option")


if __name__ == "__main__":
    main()
