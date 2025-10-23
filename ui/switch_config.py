"""
Streamlit Configuration Switcher
Automatically selects the correct config.toml based on environment.

Usage:
    python switch_config.py         # Uses ENVIRONMENT variable (dev/prod)
    python switch_config.py dev     # Force development config
    python switch_config.py prod    # Force production config
"""
import os
import shutil
import sys
from pathlib import Path


def switch_config(environment=None):
    """
    Switch Streamlit config based on environment.
    
    Args:
        environment: 'dev' or 'prod'. If None, reads from ENVIRONMENT env var.
    """
    # Determine environment
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'dev').lower()
    
    environment = environment.lower()
    
    if environment not in ['dev', 'prod', 'development', 'production']:
        print(f"⚠️  Unknown environment '{environment}', defaulting to 'dev'")
        environment = 'dev'
    
    # Normalize environment names
    if environment in ['development', 'dev']:
        env_name = 'dev'
        env_label = 'DEVELOPMENT'
    else:
        env_name = 'prod'
        env_label = 'PRODUCTION'
    
    # Define paths
    streamlit_dir = Path(__file__).parent / '.streamlit'
    source_config = streamlit_dir / f'config.{env_name}.toml'
    target_config = streamlit_dir / 'config.toml'
    
    # Check if source config exists
    if not source_config.exists():
        print(f"❌ Error: {source_config} not found!")
        return False
    
    # Copy the config file
    try:
        shutil.copy2(source_config, target_config)
        print(f"✅ Switched to {env_label} configuration")
        print(f"   Source: {source_config.name}")
        print(f"   Target: {target_config.name}")
        
        # Print key settings
        with open(target_config, 'r') as f:
            content = f.read()
            if 'showErrorDetails = true' in content:
                print(f"   • Error details: VISIBLE (dev mode)")
            else:
                print(f"   • Error details: HIDDEN (production)")
            
            if 'toolbarMode = "developer"' in content:
                print(f"   • Toolbar mode: DEVELOPER")
            elif 'toolbarMode = "minimal"' in content:
                print(f"   • Toolbar mode: MINIMAL")
        
        return True
        
    except Exception as e:
        print(f"❌ Error copying config: {e}")
        return False


if __name__ == '__main__':
    # Get environment from command line or environment variable
    env = sys.argv[1] if len(sys.argv) > 1 else None
    
    if env and env in ['--help', '-h']:
        print(__doc__)
        sys.exit(0)
    
    success = switch_config(env)
    sys.exit(0 if success else 1)
