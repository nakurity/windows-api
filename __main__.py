import asyncio

from pathlib import Path
from nakuritycore.utils.config import get_config_loader

# Load configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
config = get_config_loader(
    PROJECT_ROOT / "src" / "resources" / "authentication.yaml"
).config.get("debug", {})

if __name__ == "__main__":
    from src.dev.nakurity import WindowsAPIServer
    asyncio.run( # Launch Windows API server
        WindowsAPIServer().start()
    )