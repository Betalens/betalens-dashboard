"""Launch the independently installed research API."""
import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Betalens research workbench API")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--factor-root", default=os.environ.get("BETALENS_FACTOR_ROOT"))
    serve.add_argument("--runtime-dir", default=os.environ.get("BETALENS_RUNTIME_DIR"))
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    if not args.factor_root or not Path(args.factor_root).expanduser().is_dir():
        parser.error("--factor-root or BETALENS_FACTOR_ROOT must point to an existing research checkout")
    os.environ["BETALENS_FACTOR_ROOT"] = str(Path(args.factor_root).expanduser().resolve())
    if args.runtime_dir:
        os.environ["BETALENS_RUNTIME_DIR"] = str(Path(args.runtime_dir).expanduser().resolve())
    import uvicorn
    uvicorn.run("dashboard.backend.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
