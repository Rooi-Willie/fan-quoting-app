#!/usr/bin/env python3
"""
Step 4: Deploy UI to Streamlit Cloud
Provides instructions for manual Streamlit Cloud deployment
"""

import sys
import yaml
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from utils.logger import Logger


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_streamlit_secrets():
    """Create .streamlit/secrets.toml file"""
    logger = Logger()
    config = load_config()
    
    api_url = config['api'].get('url', 'YOUR_API_URL_HERE')
    api_key = config['api']['api_key']
    
    secrets_content = f"""# Streamlit Secrets Configuration
# This file is for LOCAL DEVELOPMENT ONLY
# DO NOT commit to git!

# API Configuration
API_BASE_URL = "{api_url}"
API_KEY = "{api_key}"
"""
    
    secrets_dir = Path("fan-quoting-app/ui/.streamlit")
    secrets_dir.mkdir(parents=True, exist_ok=True)
    
    secrets_file = secrets_dir / "secrets.toml"
    secrets_file.write_text(secrets_content)
    
    logger.success(f"Created {secrets_file}")
    logger.warning("Remember: This file is gitignored for security")


def main():
    logger = Logger()
    logger.header("UI DEPLOYMENT TO STREAMLIT CLOUD")
    
    config = load_config()
    api_url = config['api'].get('url', 'Not deployed yet')
    api_key = config['api']['api_key']
    streamlit_config = config['streamlit']
    domain_config = config['domain']
    
    logger.section("DEPLOYMENT CHECKLIST")
    
    # Step 1: Create local secrets file
    logger.step(1, 6, "Creating local secrets file")
    create_streamlit_secrets()
    
    # Step 2: Prepare repository
    logger.step(2, 6, "Preparing repository")
    
    logger.info("Ensure your code is committed and pushed:")
    logger.command("git add .")
    logger.command('git commit -m "Prepare for deployment"')
    logger.command("git push origin main")
    
    if not logger.confirm("\nHave you pushed to GitHub?", default=False):
        logger.warning("Please push your code to GitHub first, then run this script again")
        sys.exit(0)
    
    # Step 3: Deploy to Streamlit Cloud
    logger.step(3, 6, "Deploy to Streamlit Cloud")
    
    logger.info("\n📱 MANUAL DEPLOYMENT STEPS:")
    logger.info("")
    logger.info("1. Go to: https://share.streamlit.io")
    logger.info("2. Sign in with your GitHub account")
    logger.info("3. Click 'New app'")
    logger.info("")
    logger.info("4. Configure deployment:")
    logger.info(f"   Repository: {config['github']['repository']}")
    logger.info(f"   Branch: {config['github']['branch']}")
    logger.info("   Main file path: ui/Login_Page.py")
    logger.info(f"   App URL: {streamlit_config['app_name']}")
    logger.info("")
    logger.info("5. Click 'Advanced settings'")
    logger.info("")
    logger.info("6. Add these secrets:")
    logger.info("   ┌─────────────────────────────────────────┐")
    logger.info("   │ API_BASE_URL = \"{api_url}\"")
    logger.info(f"   │ API_KEY = \"{api_key}\"")
    logger.info("   └─────────────────────────────────────────┘")
    logger.info("")
    logger.info("7. Set Python version: 3.11")
    logger.info("")
    logger.info("8. Click 'Deploy'!")
    logger.info("")
    
    input("Press Enter when deployment is complete...")
    
    # Step 4: Configure authentication
    logger.step(4, 6, "Configure authentication")
    
    logger.info("\n🔒 SECURITY SETUP:")
    logger.info("")
    logger.info("1. In Streamlit Cloud dashboard, go to your app")
    logger.info("2. Click 'Settings' → 'Sharing'")
    logger.info("3. Enable 'Require viewers to log in'")
    logger.info("")
    logger.info("4. Add allowed email domain:")
    logger.info(f"   Domain: {streamlit_config['allowed_email_domain']}")
    logger.info("")
    logger.info("5. Save settings")
    logger.info("")
    
    input("Press Enter when authentication is configured...")
    
    # Step 5: Custom domain (optional)
    logger.step(5, 6, "Set up custom domain (optional)")
    
    if logger.confirm("\nDo you want to set up a custom domain?", default=True):
        logger.info("\n🌐 CUSTOM DOMAIN SETUP:")
        logger.info("")
        logger.info("1. In Streamlit Cloud:")
        logger.info("   - Settings → Custom domains")
        logger.info(f"   - Add domain: {domain_config['full_domain']}")
        logger.info("   - Copy the CNAME target (e.g., cname.streamlit.app)")
        logger.info("")
        logger.info("2. In Cloudflare:")
        logger.info(f"   - Go to DNS settings for {domain_config['name']}")
        logger.info("   - Add CNAME record:")
        logger.info(f"     * Type: CNAME")
        logger.info(f"     * Name: {domain_config['subdomain']}")
        logger.info("     * Target: (paste from Streamlit)")
        logger.info("     * Proxy status: DNS only (gray cloud)")
        logger.info("     * TTL: Auto")
        logger.info("")
        logger.info("3. Wait 5-15 minutes for DNS propagation")
        logger.info("")
        
        input("Press Enter when domain is configured...")
    
    # Step 6: Test deployment
    logger.step(6, 6, "Testing deployment")
    
    streamlit_url = logger.prompt(
        "Enter your Streamlit app URL",
        default=f"https://{streamlit_config['app_name']}.streamlit.app"
    )
    
    logger.info(f"\n🧪 Testing {streamlit_url}...")
    
    try:
        import requests
        response = requests.get(streamlit_url, timeout=10)
        if response.status_code == 200:
            logger.success("✓ App is accessible")
        else:
            logger.warning(f"App returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"Could not test automatically: {e}")
        logger.info("Please test manually in your browser")
    
    # Summary
    logger.section("DEPLOYMENT COMPLETE!")
    
    logger.summary({
        "App URL": streamlit_url,
        "Custom Domain": domain_config['full_domain'] if logger.confirm("Did you set up custom domain?", False) else "Not configured",
        "Authentication": f"Only {streamlit_config['allowed_email_domain']} emails",
        "API Backend": api_url,
        "Status": "✓ Running"
    })
    
    logger.info("\nImportant URLs:")
    logger.info(f"  UI: {streamlit_url}")
    logger.info(f"  API: {api_url}")
    logger.info(f"  API Docs: {api_url}/docs")
    logger.info("  Streamlit Dashboard: https://share.streamlit.io/")
    
    logger.info("\nAccess Instructions:")
    logger.info(f"  1. Visit: {streamlit_url}")
    logger.info("  2. Sign in with Google (using @{streamlit_config['allowed_email_domain']} email)")
    logger.info("  3. Start quoting!")
    
    logger.success("\n🎉 Full deployment complete!")
    logger.info("\nNext steps:")
    logger.info("  - Test the application end-to-end")
    logger.info("  - Use python deploy/5_monitor.py to view logs")
    logger.info("  - Use python deploy/6_manage_resources.py to manage costs")


if __name__ == "__main__":
    main()
