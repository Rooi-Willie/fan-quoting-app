"""
Google Cloud Platform helper utilities
Wraps gcloud SDK for easier deployment automation
"""

import subprocess
import json
import time
from .logger import Logger

class GCPHelper:
    """Helper class for Google Cloud Platform operations"""
    
    def __init__(self, project_id, region):
        self.project_id = project_id
        self.region = region
        self.logger = Logger()
    
    def run_command(self, command, check=True, capture_output=True):
        """Run a shell command and return output"""
        self.logger.debug(f"Running: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                capture_output=capture_output,
                text=True
            )
            return result.stdout.strip() if capture_output else None
        except subprocess.CalledProcessError as e:
            if check:
                self.logger.error(f"Command failed: {e.stderr}")
                raise
            return None
    
    def set_project(self):
        """Set the active GCP project"""
        self.run_command(f"gcloud config set project {self.project_id}")
        self.logger.success(f"Set project to {self.project_id}")
    
    def enable_api(self, api_name):
        """Enable a GCP API"""
        self.logger.info(f"Enabling {api_name}...")
        self.run_command(f"gcloud services enable {api_name} --quiet")
    
    def create_sql_instance(self, instance_name, config):
        """Create a Cloud SQL instance"""
        cmd = f"""gcloud sql instances create {instance_name} \
            --database-version={config['version']} \
            --tier={config['tier']} \
            --region={self.region} \
            --root-password={config['credentials']['root_password']} \
            --storage-size={config['storage_gb']}GB \
            --storage-type={config['storage_type']} \
            --backup-start-time={config['backup']['start_time']} \
            --maintenance-window-day={config['maintenance']['day']} \
            --maintenance-window-hour={config['maintenance']['hour']} \
            --assign-ip \
            --authorized-networks=0.0.0.0/0 \
            --quiet"""
        
        self.run_command(cmd)
    
    def instance_exists(self, instance_name):
        """Check if Cloud SQL instance exists"""
        result = self.run_command(
            f"gcloud sql instances list --filter='name:{instance_name}' --format='value(name)'",
            check=False
        )
        return bool(result and result.strip())
    
    def database_exists(self, instance_name, database_name):
        """Check if database exists"""
        result = self.run_command(
            f"gcloud sql databases list --instance={instance_name} --filter='name:{database_name}' --format='value(name)'",
            check=False
        )
        return bool(result and result.strip())
    
    def create_database(self, instance_name, database_name):
        """Create a database"""
        self.run_command(f"gcloud sql databases create {database_name} --instance={instance_name}")
    
    def create_sql_user(self, instance_name, username, password):
        """Create a database user"""
        self.run_command(
            f"gcloud sql users create {username} --instance={instance_name} --password={password}"
        )
    
    def user_exists(self, instance_name, username):
        """Check if user exists"""
        result = self.run_command(
            f"gcloud sql users list --instance={instance_name} --filter='name:{username}' --format='value(name)'",
            check=False
        )
        return bool(result and result.strip())
    
    def update_user_password(self, instance_name, username, password):
        """Update user password"""
        self.run_command(
            f"gcloud sql users set-password {username} --instance={instance_name} --password={password}"
        )
    
    def create_secret(self, secret_name, secret_value):
        """Create a secret in Secret Manager"""
        # Check if secret exists
        exists = self.run_command(
            f"gcloud secrets list --filter='name:{secret_name}' --format='value(name)'",
            check=False
        )
        
        if exists and exists.strip():
            self.logger.warning(f"Secret {secret_name} already exists, updating...")
            # Add new version
            process = subprocess.Popen(
                f"gcloud secrets versions add {secret_name} --data-file=-",
                shell=True,
                stdin=subprocess.PIPE
            )
            process.communicate(input=secret_value.encode())
        else:
            # Create new secret
            process = subprocess.Popen(
                f"gcloud secrets create {secret_name} --data-file=-",
                shell=True,
                stdin=subprocess.PIPE
            )
            process.communicate(input=secret_value.encode())
    
    def grant_secret_access(self, secret_name, service_account):
        """Grant service account access to secret"""
        cmd = f"gcloud secrets add-iam-policy-binding {secret_name} --member=serviceAccount:{service_account} --role=roles/secretmanager.secretAccessor --quiet"
        self.run_command(cmd)
    
    def deploy_cloud_run(self, service_name, config, env_vars, secrets):
        """Deploy a Cloud Run service"""
        # Build environment variables string
        env_str = ",".join([f"{k}={v}" for k, v in env_vars.items()])
        secrets_str = ",".join([f"{k}={v}:latest" for k, v in secrets.items()])
        
        cmd = f"""gcloud run deploy {service_name} \
            --source . \
            --platform managed \
            --region {self.region} \
            --allow-unauthenticated \
            --min-instances {config['min_instances']} \
            --max-instances {config['max_instances']} \
            --memory {config['memory']} \
            --cpu {config['cpu']} \
            --port {config['port']} \
            --timeout {config['timeout']} \
            --set-env-vars '{env_str}' \
            --set-secrets '{secrets_str}' \
            --quiet"""
        
        self.run_command(cmd)
    
    def get_service_url(self, service_name):
        """Get Cloud Run service URL"""
        return self.run_command(
            f"gcloud run services describe {service_name} --region={self.region} --format='value(status.url)'"
        )
    
    def service_exists(self, service_name):
        """Check if Cloud Run service exists"""
        result = self.run_command(
            f"gcloud run services list --filter='metadata.name:{service_name}' --format='value(metadata.name)'",
            check=False
        )
        return bool(result and result.strip())
    
    def delete_service(self, service_name):
        """Delete Cloud Run service"""
        self.run_command(f"gcloud run services delete {service_name} --region={self.region} --quiet")
    
    def delete_sql_instance(self, instance_name):
        """Delete Cloud SQL instance"""
        self.run_command(f"gcloud sql instances delete {instance_name} --quiet")
    
    def delete_secret(self, secret_name):
        """Delete a secret"""
        self.run_command(f"gcloud secrets delete {secret_name} --quiet", check=False)
    
    def get_instance_status(self, instance_name):
        """Get Cloud SQL instance status"""
        return self.run_command(
            f"gcloud sql instances describe {instance_name} --format='value(state)'",
            check=False
        )
    
    def start_instance(self, instance_name):
        """Start Cloud SQL instance"""
        self.run_command(
            f"gcloud sql instances patch {instance_name} --activation-policy=ALWAYS --quiet"
        )
    
    def stop_instance(self, instance_name):
        """Stop Cloud SQL instance"""
        self.run_command(
            f"gcloud sql instances patch {instance_name} --activation-policy=NEVER --quiet"
        )
    
    def update_service_instances(self, service_name, min_instances):
        """Update Cloud Run min instances"""
        self.run_command(
            f"gcloud run services update {service_name} --min-instances={min_instances} --region={self.region} --quiet"
        )
    
    def create_storage_bucket(self, bucket_name):
        """Create Cloud Storage bucket"""
        exists = self.run_command(
            f"gsutil ls -b gs://{bucket_name}",
            check=False
        )
        
        if not exists:
            self.run_command(f"gsutil mb -p {self.project_id} -l {self.region} gs://{bucket_name}")
            self.logger.success(f"Created bucket: {bucket_name}")
        else:
            self.logger.info(f"Bucket already exists: {bucket_name}")
    
    def upload_to_bucket(self, local_path, bucket_name, remote_path):
        """Upload file to Cloud Storage"""
        self.run_command(f"gsutil cp {local_path} gs://{bucket_name}/{remote_path}")
    
    def wait_for_operation(self, operation_type, timeout=300):
        """Wait for an operation to complete"""
        self.logger.info(f"Waiting for {operation_type} to complete (max {timeout}s)...")
        time.sleep(5)  # Initial wait
