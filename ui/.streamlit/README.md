# Streamlit Configuration Management

This folder contains environment-specific Streamlit configurations.

## Files

- **`config.toml`** - Active configuration (default: development)
- **`config.dev.toml`** - Development configuration (full toolbar, detailed errors)
- **`config.prod.toml`** - Production configuration (minimal UI, hidden errors)

## Quick Start

### Local Development (default)
The default `config.toml` is already set for development. Just run:
```bash
streamlit run Login_Page.py
```

### Switch to Production Mode Locally
```bash
python switch_config.py prod
streamlit run Login_Page.py
```

### Switch Back to Development Mode
```bash
python switch_config.py dev
streamlit run Login_Page.py
```

### Docker/Production Deployment
The Dockerfile automatically switches to production config during build.
No manual intervention needed.

## Configuration Differences

### Development (`config.dev.toml`)
- ✅ `showErrorDetails = true` - See full error messages for debugging
- ✅ `toolbarMode = "developer"` - Full developer toolbar with all controls
- ✅ `runOnSave = true` - Auto-reload on file changes

### Production (`config.prod.toml`)
- 🔒 `showErrorDetails = false` - Hide error details from users (security)
- 🔒 `toolbarMode = "minimal"` - Clean, minimal UI for end users
- 🔒 `runOnSave = false` - No auto-reload (performance)

## Environment Variable

You can also set the `ENVIRONMENT` variable:
```bash
# Windows CMD
set ENVIRONMENT=prod
python switch_config.py

# Windows PowerShell
$env:ENVIRONMENT="prod"
python switch_config.py

# Linux/Mac
export ENVIRONMENT=prod
python switch_config.py
```

## How It Works

1. `switch_config.py` reads the environment (from CLI arg or `ENVIRONMENT` env var)
2. Copies the appropriate config file (`config.dev.toml` or `config.prod.toml`)
3. Overwrites `config.toml` with the selected configuration
4. Streamlit reads `config.toml` on startup

## Notes

- The default `config.toml` is set to **development mode** for local work
- Docker builds automatically use **production mode** via the Dockerfile
- Never edit `config.toml` directly - edit `config.dev.toml` or `config.prod.toml` instead
- After switching configs, you need to restart Streamlit for changes to take effect
