import asyncio
import json
import traceback
import importlib
import pkgutil
import signal
from pathlib import Path

import pyautogui
import websockets

from nakuritycore.utils.config import get_config_loader

class WindowsAPIServer:
    def __init__(self, config_path: Path):
        # ---------------------------
        # Load configuration
        # ---------------------------
        self.cfg = get_config_loader(config_path).config
        self.host = self.cfg.get("host", "127.0.0.1")
        self.port = int(self.cfg.get("port", 8765))
        self.auth_token = self.cfg.get("auth_token", "replace-with-a-strong-secret")
        self.screenshot_dir = Path(self.cfg.get("screenshot_dir", "./screenshots"))

        # Safety defaults
        pyautogui.FAILSAFE = bool(self.cfg.get("failsafe", True))
        pyautogui.PAUSE = float(self.cfg.get("pause", 0.05))

        # Ensure screenshot directory exists
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Handlers
        self.handlers = {}
        self.load_handlers()

        # Shutdown event
        self.shutdown_event = asyncio.Event()

    # ---------------------------
    # Dynamic handler loader
    # ---------------------------
    def load_handlers(self):
        from . import handlers as package
        self.handlers.clear()
        for _, modname, _ in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{__package__}.handlers.{modname}")
            if hasattr(module, "handle"):
                self.handlers[modname] = module.handle

    # ---------------------------
    # Utilities
    # ---------------------------
    def ok(self, payload=None):
        return json.dumps({"status": "ok", "result": payload or {}})

    def err(self, message, details=None):
        return json.dumps({"status": "error", "error": {"message": message, "details": details or ""}})

    # ---------------------------
    # Message dispatcher
    # ---------------------------
    async def handle_message(self, msg: dict) -> str:
        if msg.get("token") != self.auth_token:
            return self.err("unauthorized")

        action = msg.get("action")
        if not action or not isinstance(action, str):
            return self.err("invalid_action", "Missing or non-string 'action'")

        # Dynamic reload
        if action == "reload":
            try:
                self.load_handlers()
                return self.ok({"message": "Handlers reloaded", "count": len(self.handlers)})
            except Exception as e:
                return self.err("reload_failed", {"exception": str(e), "traceback": traceback.format_exc()})

        # Shutdown
        elif action == "shutdown":
            self.shutdown_event.set()
            return self.ok({"message": "Shutting down"})

        # Other handlers
        handler = self.handlers.get(action)
        if not handler:
            return self.err("unsupported_action", f"Action '{action}' not supported")

        try:
            result = await handler(msg, {"screenshot_dir": self.screenshot_dir})
            return json.dumps(result)
        except Exception as e:
            return self.err("executionerror", {"exception": str(e), "traceback": traceback.format_exc()})

    # ---------------------------
    # WebSocket handler
    # ---------------------------
    async def websocket_handler(self, websocket):
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send(self.err("invalid_json"))
                continue
            response = await self.handle_message(data)
            await websocket.send(response)

    # ---------------------------
    # Server main loop
    # ---------------------------
    async def start(self):
        server = await websockets.serve(self.websocket_handler, self.host, self.port, max_size=2**20)
        print(f"WebSocket GUI server listening on ws://{self.host}:{self.port}")
        print("Press Ctrl+C to stop.")

        await self.shutdown_event.wait()

        print("[SHUTDOWN] Closing WebSocket server...")
        server.close()
        await server.wait_closed()
        print("[SHUTDOWN] Server closed successfully")

    # ---------------------------
    # Signal handler
    # ---------------------------
    def setup_signal_handlers(self):
        def handler(sig, frame):
            print("\n[SHUTDOWN] Received shutdown signal, closing server...")
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(self.shutdown_event.set)

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)


if __name__ == "__main__":
    config_path = Path(__file__).parents[3] / "resources" / "authentication.yaml"
    server = WindowsAPIServer(config_path)
    server.setup_signal_handlers()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        print("[SHUTDOWN] Cleanup complete")

__all__ = ["WindowsAPIServer"]