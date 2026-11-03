"""Tests para la validación de initData de Telegram."""
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.core.security import validate_init_data, TelegramAuthError

FAKE_BOT_TOKEN = "7777777777:AAFake_Test_Token_For_Unit_Tests_Only"


def _build_init_data(bot_token: str, user: dict, tamper_hash: bool = False) -> str:
    """Genera un initData firmado con el bot_token dado."""
    auth_date = str(int(time.time()))
    user_json = json.dumps(user, separators=(",", ":"))

    params = {
        "auth_date": auth_date,
        "user": user_json,
        "query_id": "AAHdF6IQAAAAAN0XohA",
    }

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if tamper_hash:
        computed_hash = "a" * 64  # hash falso

    params["hash"] = computed_hash
    return urlencode(params)


class TestValidateInitData:
    def test_valid_init_data(self):
        user = {"id": 123456, "first_name": "Gustavo", "username": "gus"}
        init_data = _build_init_data(FAKE_BOT_TOKEN, user)
        result = validate_init_data(init_data, bot_token=FAKE_BOT_TOKEN)
        assert result["id"] == 123456
        assert result["first_name"] == "Gustavo"

    def test_tampered_hash_fails(self):
        user = {"id": 123456, "first_name": "Gustavo", "username": "gus"}
        init_data = _build_init_data(FAKE_BOT_TOKEN, user, tamper_hash=True)
        with pytest.raises(TelegramAuthError, match="hash inválido"):
            validate_init_data(init_data, bot_token=FAKE_BOT_TOKEN)

    def test_empty_init_data_fails(self):
        with pytest.raises(TelegramAuthError, match="vacío"):
            validate_init_data("", bot_token=FAKE_BOT_TOKEN)

    def test_missing_hash_fails(self):
        init_data = urlencode({"auth_date": str(int(time.time())), "user": '{"id":1}'})
        with pytest.raises(TelegramAuthError, match="hash ausente"):
            validate_init_data(init_data, bot_token=FAKE_BOT_TOKEN)
