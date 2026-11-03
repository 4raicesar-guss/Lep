import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.core.config import get_settings


class TelegramAuthError(Exception):
    pass


def validate_init_data(init_data: str, bot_token: str | None = None) -> dict:
    """Valida initData de Telegram WebApp según la spec oficial.

    Retorna el objeto user parseado si la validación es exitosa.
    Lanza TelegramAuthError si falla.
    """
    if bot_token is None:
        bot_token = get_settings().bot_token

    parsed = parse_qsl(init_data, keep_blank_values=True)

    if not parsed:
        raise TelegramAuthError("initData vacío o malformado")

    data_dict: dict[str, str] = {}
    received_hash = ""

    for key, value in parsed:
        if key == "hash":
            received_hash = value
        else:
            data_dict[key] = value

    if not received_hash:
        raise TelegramAuthError("hash ausente en initData")

    # data_check_string: pares key=value ordenados por key, separados por \n
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data_dict.items())
    )

    # secret_key = HMAC-SHA256(key=b"WebAppData", msg=bot_token)
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()

    # hash calculado = HMAC-SHA256(key=secret_key, msg=data_check_string)
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise TelegramAuthError("hash inválido")

    # Validar auth_date
    auth_date_str = data_dict.get("auth_date")
    if auth_date_str is None:
        raise TelegramAuthError("auth_date ausente")

    try:
        auth_date = int(auth_date_str)
    except ValueError:
        raise TelegramAuthError("auth_date no es un entero válido")

    if time.time() - auth_date > get_settings().auth_timeout:
        raise TelegramAuthError("auth_date expirado (>24h)")

    # Parsear user
    user_str = data_dict.get("user")
    if user_str is None:
        raise TelegramAuthError("campo user ausente")

    try:
        user = json.loads(user_str)
    except json.JSONDecodeError:
        raise TelegramAuthError("campo user no es JSON válido")

    return user
