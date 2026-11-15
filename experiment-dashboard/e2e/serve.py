"""Serve this checkout's built UI over an isolated core archive API."""
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import uvicorn
from betalens.experiments.api import create_app

root = Path(__file__).resolve().parents[2]
app = create_app(root / "outputs/experiments-e2e")
app.router.routes[:] = [route for route in app.router.routes if getattr(route, "name", None) != "viewer"]
app.mount("/", StaticFiles(directory=root / "dist/experiment-viewer", html=True), name="viewer")
uvicorn.run(app, host="127.0.0.1", port=8021)
