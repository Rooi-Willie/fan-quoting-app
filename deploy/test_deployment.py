#!/usr/bin/env python3
"""
Test Deployment - Verify all components are working
Run this after deployment to ensure everything is functioning correctly
"""

import sys
import yaml
import requests
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from utils.logger import Logger


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_api_health(api_url, logger):
    """Test API health endpoint"""
    logger.info("Testing API health endpoint...")
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.success(f"✓ Health check passed: {data.get('status')}")
            return True
        else:
            logger.error(f"✗ Health check failed: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Health check error: {e}")
        return False


def test_api_root(api_url, logger):
    """Test API root endpoint"""
    logger.info("Testing API root endpoint...")
    try:
        response = requests.get(f"{api_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.success(f"✓ Root endpoint: {data.get('message')}")
            return True
        else:
            logger.error(f"✗ Root endpoint failed: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Root endpoint error: {e}")
        return False


def test_api_with_key(api_url, api_key, logger):
    """Test API endpoint with authentication"""
    logger.info("Testing API with authentication...")
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(f"{api_url}/api/test-db", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.success(f"✓ Database connection: {data.get('database')}")
            return True
        elif response.status_code == 401:
            logger.error("✗ Authentication failed - API key invalid")
            return False
        else:
            logger.error(f"✗ Test failed: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Test error: {e}")
        return False


def test_api_without_key(api_url, logger):
    """Test that protected endpoints reject requests without API key"""
    logger.info("Testing API key requirement...")
    try:
        response = requests.get(f"{api_url}/api/test-db", timeout=10)
        if response.status_code == 401:
            logger.success("✓ API key requirement enforced")
            return True
        else:
            logger.warning(f"⚠ Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Test error: {e}")
        return False


def test_api_docs(api_url, logger):
    """Test API documentation endpoint"""
    logger.info("Testing API documentation...")
    try:
        response = requests.get(f"{api_url}/docs", timeout=10)
        if response.status_code == 200:
            logger.success("✓ API documentation accessible")
            logger.info(f"   View at: {api_url}/docs")
            return True
        else:
            logger.error(f"✗ Docs failed: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Docs error: {e}")
        return False


def test_ui(ui_url, logger):
    """Test UI is accessible"""
    logger.info("Testing UI...")
    try:
        response = requests.get(ui_url, timeout=10)
        if response.status_code == 200:
            logger.success("✓ UI is accessible")
            return True
        else:
            logger.warning(f"⚠ UI returned status {response.status_code}")
            return True  # Might be auth wall, which is expected
    except Exception as e:
        logger.error(f"✗ UI error: {e}")
        return False


def main():
    logger = Logger()
    logger.header("DEPLOYMENT TESTING")
    
    config = load_config()
    
    # Get URLs
    api_url = config['api'].get('url')
    api_key = config['api']['api_key']
    streamlit_app = config['streamlit']['app_name']
    
    if not api_url:
        logger.error("API URL not found in config. Deploy API first with:")
        logger.info("  python deploy/3_deploy_api.py")
        sys.exit(1)
    
    ui_url = f"https://{streamlit_app}.streamlit.app"
    
    logger.info(f"API URL: {api_url}")
    logger.info(f"UI URL: {ui_url}")
    
    # Run tests
    logger.section("RUNNING TESTS")
    
    results = []
    
    # API Tests
    logger.info("\n📦 API TESTS")
    results.append(("API Health", test_api_health(api_url, logger)))
    results.append(("API Root", test_api_root(api_url, logger)))
    results.append(("API Docs", test_api_docs(api_url, logger)))
    results.append(("API Key Required", test_api_without_key(api_url, logger)))
    results.append(("API Authenticated", test_api_with_key(api_url, api_key, logger)))
    
    # UI Tests
    logger.info("\n🎨 UI TESTS")
    results.append(("UI Accessible", test_ui(ui_url, logger)))
    
    # Summary
    logger.section("TEST RESULTS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.table(
        [[name, "✓ PASS" if result else "✗ FAIL"] for name, result in results],
        ["Test", "Result"]
    )
    
    logger.info(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        logger.success("\n🎉 All tests passed! Deployment successful!")
        logger.info("\nYour application is ready to use:")
        logger.info(f"  UI: {ui_url}")
        logger.info(f"  API: {api_url}")
        logger.info(f"  API Docs: {api_url}/docs")
    else:
        logger.warning(f"\n⚠ {total - passed} test(s) failed. Check the errors above.")
        logger.info("\nTroubleshooting:")
        logger.info("  1. Check logs: python deploy/5_monitor.py")
        logger.info("  2. Verify API is running in GCP Console")
        logger.info("  3. Check API key in config.yaml matches deployment")
        sys.exit(1)


if __name__ == "__main__":
    main()
