"""Manual launch script for the CLM-05 experimental API."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn

from mindtune_clm.api.app import create_app
from mindtune_clm.api.config import CLM05APIConfig


def _ensure_env(args: argparse.Namespace) -> None:
    if args.store:
        os.environ["CLM05_API_STORE"] = args.store
    if args.token:
        os.environ["CLM05_API_TOKEN"] = args.token
    if args.host:
        os.environ["CLM05_API_HOST"] = args.host
    if args.port:
        os.environ["CLM05_API_PORT"] = str(args.port)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CLM-05 experimental API")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8005, help="Bind port")
    parser.add_argument("--store", default=None, help="SQLite store path or directory")
    parser.add_argument("--token", default=None, help="Optional static bearer token")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload")
    args = parser.parse_args()

    _ensure_env(args)
    config = CLM05APIConfig.from_env()
    app = create_app(config)

    store_path = Path(config.store_path) if config.store_path else Path(".") / "clm05_store.sqlite"
    print(f"CLM-05 API starting on {args.host}:{args.port}")
    print(f"Store path: {store_path}")
    print(f"Auth token configured: {'yes' if config.bearer_token else 'no'}")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
