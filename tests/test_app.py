from bot.journal import Journal
from bot.main import build_application


def test_application_builds_with_all_commands(tmp_path):
    app = build_application("123456:TEST_TOKEN_NOT_REAL", "Asia/Kolkata", Journal(tmp_path / "t.db"))
    commands = {
        cmd for handlers in app.handlers.values() for h in handlers for cmd in getattr(h, "commands", [])
    }
    assert {"start", "gold", "session", "news", "size", "spread", "log", "result", "journal", "whoami"} <= commands
