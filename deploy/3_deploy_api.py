#!/usr/bin/env python3
"""
Step 3: Deploy API to Cloud Run
Builds and deploys the FastAPI application
"""

import sys
import yaml
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from utils.logger import Logger
from utils.gcp_helper import GCPHelper


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_production_dockerfile():
    """Create optimized Dockerfile for Cloud Run"""
    logger = Logger()
    logger.info("Creating production Dockerfile...")
    
    dockerfile_content = """FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=2)"

# Expose port
EXPOSE 8080

# Run application
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1
"""
    
    dockerfile_path = Path("fan-quoting-app/api/Dockerfile.production")
    dockerfile_path.write_text(dockerfile_content)
    
    logger.success("Dockerfile created")


def test_api_endpoint(url):
    """Test deployed API"""
    import requests
    
    logger = Logger()
    logger.info("Testing API endpoints...")
    
    tests = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api/test-db", "Database connection")
    ]
    
    results = []
    for endpoint, description in tests:
        try:
            response = requests.get(f"{url}{endpoint}", timeout=10)
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
    logger.info("  1. Build Docker container")
    logger.info("  2. Push to Google Container Registry")
    logger.info("  3. Deploy to Cloud Run")
    logger.info("  4. Configure environment variables")
    logger.info("  5. Test deployment")
    
    logger.warning(f"\nEstimated time: 5-10 minutes")
    
    if not logger.confirm("\nProceed with deployment?", default=True):
        logger.warning("Deployment cancelled")
        sys.exit(0)
    
    # Change to API directory
    api_dir = Path("fan-quoting-app/api")
    if not api_dir.exists():
        logger.exit_with_error(f"API directory not found: {api_dir}")
    
    original_dir = os.getcwd()
    os.chdir(api_dir)
    
    try:
        # Step 1: Build and deploy
        logger.step(1, 5, "Building and deploying to Cloud Run")
        logger.info("This may take 5-10 minutes on first deployment...")
        
        # Prepare environment variables
        cloud_sql_connection = f"{project_id}:{region}:{db_config['instance_name']}"
        
        env_vars = {
            "CLOUD_SQL_CONNECTION_NAME": cloud_sql_connection,
            "DB_USER": db_config['credentials']['app_user'],
            "DB_NAME": db_config['database_name'],
            "ENVIRONMENT": api_config['environment']
        }
        
        secrets = {
            "DB_PASSWORD": "db-password",
            "API_KEY": "api-key"
        }
        
        # Deploy using gcloud
        logger.info("Starting deployment...")
        
        env_str = ",".join([f"{k}={v}" for k, v in env_vars.items()])
        secrets_str = ",".join([f"{k}={v}:latest" for k, v in secrets.items()])
        
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
            --set-env-vars "{env_str}" \
            --set-secrets "{secrets_str}" \
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
        
        if test_api_endpoint(api_url):
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
