#!/usr/bin/env python3
"""
Step 6: Manage Cloud Resources
Start/stop services and configure auto-shutdown
"""

import sys
import yaml
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from utils.logger import Logger
from utils.gcp_helper import GCPHelper


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_config(config):
    """Save configuration"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def setup_windows_scheduler(config, action):
    """Set up Windows Task Scheduler for auto-shutdown"""
    logger = Logger()
    
    if action == "enable":
        logger.info("Setting up Windows Task Scheduler...")
        
        schedule = config['cost_optimization']['auto_shutdown']['schedule']
        script_path = Path(__file__).resolve()
        
        # Stop schedule
        stop_days = ",".join(schedule['stop']['days'])
        stop_time = schedule['stop']['time']
        
        # Start schedule
        start_days = ",".join(schedule['start']['days'])
        start_time = schedule['start']['time']
        
        logger.info("\n📋 To set up automated schedule:")
        logger.info("1. Open Task Scheduler (taskschd.msc)")
        logger.info("2. Create two tasks:")
        logger.info("")
        logger.info("   Task 1: Stop Services")
        logger.info(f"   - Trigger: Weekly on {stop_days} at {stop_time}")
        logger.info(f"   - Action: python {script_path} --action stop")
        logger.info("")
        logger.info("   Task 2: Start Services")
        logger.info(f"   - Trigger: Weekly on {start_days} at {start_time}")
        logger.info(f"   - Action: python {script_path} --action start")
        logger.info("")
        
        # Update config
        config['cost_optimization']['auto_shutdown']['enabled'] = True
        save_config(config)
        
        logger.success("Auto-shutdown enabled in config")
        logger.warning("Please create the scheduled tasks manually as shown above")
    
    else:  # disable
        config['cost_optimization']['auto_shutdown']['enabled'] = False
        save_config(config)
        logger.success("Auto-shutdown disabled in config")
        logger.info("You can manually delete the scheduled tasks if created")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage cloud resources")
    parser.add_argument("--action", choices=["start", "stop", "status", "schedule-enable", "schedule-disable"])
    args = parser.parse_args()
    
    logger = Logger()
    config = load_config()
    
    project_id = config['gcp']['project_id']
    region = config['gcp']['region']
    service_name = config['api']['service_name']
    instance_name = config['database']['instance_name']
    
    gcp = GCPHelper(project_id, region)
    gcp.set_project()
    
    if args.action == "stop":
        logger.header("STOPPING CLOUD SERVICES")
        logger.warning("This will stop the database and scale API to zero")
        
        if not logger.confirm("Proceed?", default=True):
            logger.info("Cancelled")
            sys.exit(0)
        
        # Stop database
        logger.info("Stopping Cloud SQL instance...")
        gcp.stop_instance(instance_name)
        logger.success("Database stopped")
        
        # Scale API to zero
        logger.info("Scaling API to zero...")
        gcp.update_service_instances(service_name, 0)
        logger.success("API scaled to zero")
        
        logger.section("SERVICES STOPPED")
        logger.info("Estimated savings: ~$10-15/month")
        logger.info("To restart: python deploy/6_manage_resources.py --action start")
    
    elif args.action == "start":
        logger.header("STARTING CLOUD SERVICES")
        
        # Start database
        logger.info("Starting Cloud SQL instance...")
        gcp.start_instance(instance_name)
        logger.success("Database started")
        
        # Scale API to 1
        logger.info("Starting API...")
        gcp.update_service_instances(service_name, config['api']['min_instances'])
        logger.success("API started")
        
        logger.section("SERVICES RUNNING")
        api_url = gcp.get_service_url(service_name)
        logger.info(f"API URL: {api_url}")
    
    elif args.action == "status":
        logger.header("RESOURCE STATUS")
        
        # Database
        db_status = gcp.get_instance_status(instance_name)
        logger.info(f"Database: {db_status}")
        
        # API
        if gcp.service_exists(service_name):
            api_url = gcp.get_service_url(service_name)
            logger.info(f"API: Running")
            logger.info(f"URL: {api_url}")
        else:
            logger.info("API: Not deployed")
        
        # Auto-shutdown status
        auto_shutdown = config['cost_optimization']['auto_shutdown']
        if auto_shutdown['enabled']:
            logger.info("\nAuto-shutdown: ENABLED")
            schedule = auto_shutdown['schedule']
            logger.info(f"  Stop: {schedule['stop']['days']} at {schedule['stop']['time']}")
            logger.info(f"  Start: {schedule['start']['days']} at {schedule['start']['time']}")
        else:
            logger.info("\nAuto-shutdown: DISABLED")
        
        # Cost estimate
        logger.info("\nEstimated Monthly Cost:")
        if db_status == "RUNNABLE":
            logger.info("  ~$25-30 (running)")
        else:
            logger.info("  ~$10-15 (stopped)")
    
    elif args.action == "schedule-enable":
        logger.header("ENABLE AUTO-SHUTDOWN SCHEDULE")
        setup_windows_scheduler(config, "enable")
    
    elif args.action == "schedule-disable":
        logger.header("DISABLE AUTO-SHUTDOWN SCHEDULE")
        setup_windows_scheduler(config, "disable")
    
    else:
        # Interactive mode
        logger.header("RESOURCE MANAGEMENT")
        
        logger.info("What would you like to do?")
        logger.info("  1. Start services")
        logger.info("  2. Stop services")
        logger.info("  3. Check status")
        logger.info("  4. Enable auto-shutdown schedule")
        logger.info("  5. Disable auto-shutdown schedule")
        logger.info("  6. Exit")
        
        choice = logger.prompt("\nSelect option [1-6]")
        
        if choice == "1":
            sys.argv.append("--action")
            sys.argv.append("start")
            main()
        elif choice == "2":
            sys.argv.append("--action")
            sys.argv.append("stop")
            main()
        elif choice == "3":
            sys.argv.append("--action")
            sys.argv.append("status")
            main()
        elif choice == "4":
            sys.argv.append("--action")
            sys.argv.append("schedule-enable")
            main()
        elif choice == "5":
            sys.argv.append("--action")
            sys.argv.append("schedule-disable")
            main()
        elif choice == "6":
            logger.info("Goodbye!")
        else:
            logger.warning("Invalid option")


if __name__ == "__main__":
    main()
