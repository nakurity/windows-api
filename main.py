import asyncio

from .src.dev.nakurity import WindowsAPIServer
from pathlib import Path

def main():
    config_path = Path(__file__).parent / "src" / "resources" / "authentication.yaml"
    server = WindowsAPIServer(config_path)
    server.setup_signal_handlers()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        print("[SHUTDOWN] Cleanup complete")


if __name__ == "__main__":
    main()
