#!/usr/bin/env python3
"""Genera un initData de Telegram válido, firmado con BOT_TOKEN, para pruebas sin Telegram.

Uso (desde la raíz del repo):
    python3 scripts/mock_initdata.py                       # usuario 1001 "Tester"
    python3 scripts/mock_initdata.py --id 42 --name Gaucho --username el_gaucho
    python3 scripts/mock_initdata.py --curl                # imprime un curl listo
    python3 scripts/mock_initdata.py --js                  # imprime el snippet para la consola del navegador

El token se toma de --token, de la variable BOT_TOKEN o de backend/.env.
El initData caduca según AUTH_TIMEOUT del backend (86400 s por defecto): regenéralo si expira.
Solo usa la librería estándar.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / "backend" / ".env"


def load_bot_token(cli_token: str | None) -> str:
    if cli_token:
        return cli_token
    if os.environ.get("BOT_TOKEN"):
        return os.environ["BOT_TOKEN"]
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("BOT_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("No se encontró BOT_TOKEN (usa --token, la variable de entorno o backend/.env).")


def build_init_data(bot_token: str, user: dict, auth_date: int | None = None) -> str:
    """Replica el algoritmo oficial de Telegram WebApp (igual que app/core/security.py)."""
    params = {
        "auth_date": str(auth_date or int(time.time())),
        "user": json.dumps(user, separators=(",", ":"), ensure_ascii=False),
        "query_id": "AAHmockQueryId",
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--id", type=int, default=1001, help="telegram_id del usuario simulado")
    parser.add_argument("--name", default="Tester", help="first_name")
    parser.add_argument("--username", default="tester", help="username")
    parser.add_argument("--token", help="BOT_TOKEN (por defecto: env o backend/.env)")
    parser.add_argument("--api", default="http://localhost:8000", help="URL base para --curl")
    parser.add_argument("--curl", action="store_true", help="imprime un curl a /api/player/state")
    parser.add_argument("--js", action="store_true", help="imprime el snippet para localStorage")
    args = parser.parse_args()

    token = load_bot_token(args.token)
    user = {"id": args.id, "first_name": args.name, "username": args.username, "language_code": "es"}
    init_data = build_init_data(token, user)

    if args.curl:
        print(f"curl -s {args.api}/api/player/state -H 'X-Telegram-Init-Data: {init_data}'")
    elif args.js:
        print("// Pegar en la consola del navegador (DevTools) y recargar la página:")
        print(f"localStorage.setItem('mock_init_data', {json.dumps(init_data)}); location.reload();")
    else:
        print(init_data)


if __name__ == "__main__":
    main()
