#!/usr/bin/env python3

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import webview

APP_DIR = Path(__file__).resolve().parent
PYTHON = APP_DIR / ".venv/bin/python"
SERVER = APP_DIR / "server.py"
URL = "http://127.0.0.1:8787"
LOG = Path("/tmp/mindtune_console.log")


def server_is_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", 8787)) == 0


def start_server() -> None:
    if server_is_running():
        return

    with LOG.open("ab") as log:
        subprocess.Popen(
            [str(PYTHON), str(SERVER)],
            cwd=str(APP_DIR),
            stdout=log,
            stderr=log,
            start_new_session=True,
        )

    for _ in range(40):
        if server_is_running():
            return
        time.sleep(0.25)

    raise RuntimeError(f"MindTune non si è avviato. Controlla {LOG}")


def main() -> None:
    start_server()

    webview.create_window(
        title="MindTune Lab",
        url=URL,
        width=1440,
        height=920,
        min_size=(1100, 700),
        resizable=True,
        confirm_close=False,
        text_select=True,
    )

    webview.start(gui="cocoa", private_mode=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Errore MindTune Lab: {exc}", file=sys.stderr)
        sys.exit(1)
