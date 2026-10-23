import pytest
from telegram.error import InvalidToken, NetworkError
from telegram.ext import Application

from bot import main as bot_main


@pytest.mark.parametrize(
    "error, expected",
    [(InvalidToken("secret-token-123"), "rejected the token"), (NetworkError("offline"), "Can't reach Telegram")],
)
def test_friendly_startup_errors_never_leak_token(monkeypatch, tmp_path, error, expected):
    monkeypatch.setenv("TELEGRAM_TOKEN", "123456:secret-token-123")
    monkeypatch.setenv("JOURNAL_DB", str(tmp_path / "t.db"))
    monkeypatch.setattr(bot_main, "load_dotenv", lambda **kwargs: None)

    def boom(self, *args, **kwargs):
        raise error

    monkeypatch.setattr(Application, "run_polling", boom)
    with pytest.raises(SystemExit) as exc:
        bot_main.main()
    assert expected in str(exc.value)
    assert "secret-token-123" not in str(exc.value)
