#!/usr/bin/env python3
"""
Step 3: Deploy API to Cloud Run
Builds and deploys the FastAPI application
"""

import sys
import yaml
import os
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


def test_api_endpoint(url, api_key):
    """Test deployed API"""
    import requests
    
    logger = Logger()
    logger.info("Testing API endpoints...")
    
    # Define tests - some require auth, some don't
    tests = [
        ("/", "Root endpoint", False),
        ("/health", "Health check", False),
        ("/api/test-db", "Database connection", True)
    ]
    
    results = []
    for endpoint, description, requires_auth in tests:
        try:
            headers = {}
            if requires_auth:
                headers["X-API-Key"] = api_key
            
            response = requests.get(f"{url}{endpoint}", headers=headers, timeout=10)
            if response.status_code == 200:
                logger.success(f"✓ {description}")
                results.append(True)
            else:
                logger.error(f"✗ {description} (Status: {response.status_code})")
                results.append(False)
        except Exception as e:
            logger.error(f"✗ {description}: {e}")
            results.append(False)
    
    return all(results)


def main():
    logger = Logger()
    logger.header("API DEPLOYMENT TO CLOUD RUN")
    
    # Load configuration
    config = load_config()
    
    project_id = config['gcp']['project_id']
    region = config['gcp']['region']
    api_config = config['api']
    db_config = config['database']
    service_name = api_config['service_name']
    
    # Initialize GCP helper
    gcp = GCPHelper(project_id, region)
    gcp.set_project()
    
    logger.section("DEPLOYMENT PLAN")
    logger.info("This script will:")
    logger.info("  1. Build Docker container (automatic)")
    logger.info("  2. Push to Google Container Registry")
    logger.info("  3. Deploy to Cloud Run")
    logger.info("  4. Configure environment variables")
    logger.info("  5. Test deployment")
    
    logger.warning(f"\nEstimated time: 5-10 minutes")
    logger.info("Note: Using Cloud Run's automatic source-based deployment")
    
    if not logger.confirm("\nProceed with deployment?", default=True):
        logger.warning("Deployment cancelled")
        sys.exit(0)
    
    # Change to API directory (relative to the project root)
    script_dir = Path(__file__).parent.parent  # deploy/
    project_root = script_dir.parent           # fan-quoting-app/
    api_dir = project_root / "api"
    
    if not api_dir.exists():
        logger.exit_with_error(f"API directory not found: {api_dir}")
    
    original_dir = os.getcwd()
    os.chdir(api_dir)
    
    try:
        # Check if service already exists
        logger.info("Checking for existing deployment...")
        existing_services = gcp.run_command(
            f"gcloud run services list --region {region} --format=value(name)",
            capture_output=True
        )
        
        service_exists = service_name in existing_services.split('\n') if existing_services else False
        
        if service_exists:
            logger.info(f"Service '{service_name}' already exists - will update")
        else:
            logger.info(f"Service '{service_name}' not found - will create new deployment")
        
        # Step 1: Build and deploy
        logger.step(1, 5, "Building and deploying to Cloud Run")
        logger.info("This may take 5-10 minutes on first deployment...")
        logger.info("Cloud Run will automatically detect and build your Python app...")
        
        # Prepare environment variables
        cloud_sql_connection = f"{project_id}:{region}:{db_config['instance_name']}"
        
        env_vars = {
            "CLOUD_SQL_CONNECTION_NAME": cloud_sql_connection,
            "DB_USER": db_config['credentials']['app_user'],
            "DB_NAME": db_config['database_name'],
            "ENVIRONMENT": api_config['environment']
        }
        
        # For --set-secrets, format is: ENV_VAR=SECRET_NAME:VERSION
        # where SECRET_NAME can only contain alphanumeric, hyphens, underscores
        # The VERSION should be 'latest' or a number
        secrets = [
            f"DB_PASSWORD=db-password:latest",
            f"API_KEY=api-key:latest"
        ]
        
        # Deploy using gcloud
        logger.info("Starting deployment...")
        
        env_str = ",".join([f"{k}={v}" for k, v in env_vars.items()])
        
        # Use separate --set-secrets flags for each secret
        # Format: ENV_VAR=SECRET_NAME:VERSION
        secrets_cmd = "--set-secrets DB_PASSWORD=db-password:1 --set-secrets API_KEY=api-key:1"

        
        deploy_cmd = f"""gcloud run deploy {service_name} \
            --source . \
            --platform managed \
            --region {region} \
            --allow-unauthenticated \
            --min-instances {api_config['min_instances']} \
            --max-instances {api_config['max_instances']} \
            --memory {api_config['memory']} \
            --cpu {api_config['cpu']} \
            --port {api_config['port']} \
            --timeout {api_config['timeout']} \
            --set-env-vars {env_str} \
            {secrets_cmd} \
            --add-cloudsql-instances {cloud_sql_connection} \
            --quiet"""
        
        try:
            with logger.spinner("Deploying"):
                gcp.run_command(deploy_cmd, capture_output=False)
            
            logger.success("Deployment complete!")
        
        except Exception as e:
            logger.exit_with_error(f"Deployment failed: {e}")
        
        # Step 2: Get service URL
        logger.step(2, 5, "Getting service URL")
        
        try:
            api_url = gcp.get_service_url(service_name)
            logger.success(f"API URL: {api_url}")
        except Exception as e:
            logger.exit_with_error(f"Failed to get service URL: {e}")
        
        # Step 3: Test deployment
        logger.step(3, 5, "Testing deployment")
        
        if test_api_endpoint(api_url, api_config['api_key']):
            logger.success("All tests passed!")
        else:
            logger.warning("Some tests failed. Check logs for details.")
        
        # Step 4: Save API URL to config
        logger.step(4, 5, "Saving API URL to configuration")
        
        # Update config with API URL
        config['api']['url'] = api_url
        
        config_path = Path(original_dir) / "deploy" / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.success("Configuration updated")
        
        # Step 5: Display summary
        logger.step(5, 5, "Generating deployment summary")
        
        logger.section("DEPLOYMENT SUCCESSFUL!")
        
        logger.summary({
            "Service Name": service_name,
            "API URL": api_url,
            "Region": region,
            "Min Instances": api_config['min_instances'],
            "Max Instances": api_config['max_instances'],
            "Memory": api_config['memory'],
            "Status": "✓ Running"
        })
        
        logger.info("\nNext Steps:")
        logger.info(f"  1. Test API: {api_url}/health")
        logger.info(f"  2. View docs: {api_url}/docs")
        logger.info("  3. Run: python deploy/4_deploy_ui.py")
        
        logger.info("\nImportant URLs:")
        logger.info(f"  API Base URL: {api_url}")
        logger.info(f"  Cloud Console: https://console.cloud.google.com/run/detail/{region}/{service_name}")
        
        logger.success("\nAPI deployment complete! 🚀")
    
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    main()
