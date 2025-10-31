#!/usr/bin/env python3
"""
Step 1: Initial Google Cloud Platform Setup
Run this ONCE to configure your GCP project
"""

import sys
import yaml
import secrets
import string
from pathlib import Path

# Add deploy directory to path for utils imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import Logger
from utils.gcp_helper import GCPHelper


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        Logger.exit_with_error(
            f"Configuration file not found: {config_path}\n"
            "Please create config.yaml from the template"
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_passwords(config):
    """Validate that passwords have been changed"""
    logger = Logger()
    
    # Check database passwords
    app_password = config['database']['credentials']['app_password']
    root_password = config['database']['credentials']['root_password']
    
    if "CHANGE_ME" in app_password or "CHANGE_ME" in root_password:
        logger.error("Please change the default passwords in config.yaml!")
        logger.info("Update the following fields:")
        logger.info("  - database.credentials.app_password")
        logger.info("  - database.credentials.root_password")
        sys.exit(1)
    
    logger.success("Passwords validated")


def generate_api_key():
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(48))
    return f"abf_{api_key}"  # Prefix for easy identification


def save_api_key(config, api_key):
    """Save generated API key to config"""
    config['api']['api_key'] = api_key
    
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    Logger().success("API key saved to config.yaml")


def main():
    logger = Logger()
    logger.header("GOOGLE CLOUD PLATFORM SETUP")
    
    # Load and validate configuration
    logger.info("Loading configuration...")
    config = load_config()
    
    validate_passwords(config)
    
    project_id = config['gcp']['project_id']
    region = config['gcp']['region']
    
    # Initialize GCP helper
    gcp = GCPHelper(project_id, region)
    
    logger.section("SETUP CHECKLIST")
    logger.info("This script will:")
    logger.info("  1. Login to Google Cloud")
    logger.info("  2. Create/select GCP project")
    logger.info("  3. Enable required APIs")
    logger.info("  4. Create service accounts")
    logger.info("  5. Generate API key")
    logger.info("  6. Set up budget alerts (manual step)")
    
    if not logger.confirm("\nProceed with setup?", default=True):
        logger.warning("Setup cancelled")
        sys.exit(0)
    
    # Step 1: Login
    logger.step(1, 7, "Logging in to Google Cloud...")
    try:
        gcp.run_command("gcloud auth login")
        logger.success("Logged in successfully")
    except Exception as e:
        logger.exit_with_error(f"Login failed: {e}")
    
    # Step 2: Create/set project
    logger.step(2, 7, f"Setting up project: {project_id}")
    
    # Check if project exists
    existing_projects = gcp.run_command(
        "gcloud projects list --format='value(projectId)'",
        check=False
    )
    
    if project_id not in existing_projects:
        logger.info(f"Creating new project: {project_id}")
        try:
            gcp.run_command(f'gcloud projects create {project_id} --name="ABF Fan Quoting App"')
            logger.success("Project created")
        except Exception as e:
            logger.exit_with_error(f"Failed to create project: {e}")
    else:
        logger.info("Project already exists")
    
    gcp.set_project()
    
    # Step 3: Enable billing
    logger.step(3, 7, "Setting up billing")
    logger.warning("MANUAL STEP REQUIRED:")
    logger.info("1. Open: https://console.cloud.google.com/billing/linkedaccount?project=" + project_id)
    logger.info("2. Link a billing account to this project")
    logger.info("3. You get $300 free credits for 90 days!")
    
    input("\nPress Enter when billing is linked...")
    logger.success("Billing configured")
    
    # Step 4: Enable APIs
    logger.step(4, 7, "Enabling required APIs (2-3 minutes)...")
    
    apis = [
        "sqladmin.googleapis.com",
        "run.googleapis.com",
        "secretmanager.googleapis.com",
        "cloudbuild.googleapis.com",
        "compute.googleapis.com",
        "storage-api.googleapis.com"
    ]
    
    with logger.spinner("Enabling APIs"):
        for api in apis:
            gcp.enable_api(api)
    
    logger.success("All APIs enabled")
    
    # Step 5: Create service account
    logger.step(5, 7, "Creating service account...")
    
    sa_name = "cloud-run-deployer"
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
    
    existing_sa = gcp.run_command(
        f"gcloud iam service-accounts list --filter='email:{sa_email}' --format='value(email)'",
        check=False
    )
    
    if not existing_sa:
        gcp.run_command(
            f'gcloud iam service-accounts create {sa_name} --display-name="Cloud Run Deployer"'
        )
        logger.success("Service account created")
    else:
        logger.info("Service account already exists")
    
    # Grant permissions
    logger.info("Granting permissions...")
    roles = [
        "roles/cloudsql.client",
        "roles/secretmanager.secretAccessor",
        "roles/run.admin"
    ]
    
    for role in roles:
        gcp.run_command(
            f'gcloud projects add-iam-policy-binding {project_id} '
            f'--member="serviceAccount:{sa_email}" --role={role} --quiet',
            check=False
        )
    
    logger.success("Permissions granted")
    
    # Step 6: Generate API key
    logger.step(6, 7, "Generating API key...")
    
    if not config['api'].get('api_key'):
        api_key = generate_api_key()
        save_api_key(config, api_key)
        logger.success(f"API Key: {api_key}")
        logger.warning("Save this key securely! It's stored in config.yaml")
    else:
        logger.info("API key already exists in config")
        logger.info(f"Current key: {config['api']['api_key']}")
    
    # Step 7: Budget alerts
    logger.step(7, 7, "Setting up budget alerts")
    logger.warning("MANUAL STEP:")
    logger.info("1. Open: https://console.cloud.google.com/billing/budgets")
    logger.info(f"2. Create budget: ${config['monitoring']['budget']['monthly_limit_usd']}/month")
    logger.info(f"3. Set alerts at: {config['monitoring']['budget']['alert_thresholds']}%")
    
    # Summary
    logger.section("SETUP COMPLETE!")
    logger.summary({
        "Project ID": project_id,
        "Region": region,
        "APIs Enabled": "✓",
        "Service Account": "✓",
        "API Key": "✓ (in config.yaml)"
    })
    
    logger.info("\nNext Steps:")
    logger.info("  1. Set up budget alerts (links above)")
    logger.info("  2. Run: python deploy/2_init_database.py")
    logger.success("\nGCP setup complete! 🎉")


if __name__ == "__main__":
    main()
