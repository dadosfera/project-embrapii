from pathlib import Path
import subprocess
import sys


def test_only_adapters_import_src_modules():
    root = Path(__file__).parents[1]
    offenders = []
    for path in root.rglob("*.py"):
        if "adapters" in path.parts or "tests" in path.parts:
            continue
        if "src." in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(root))
    assert offenders == []


def test_chat_adapter_and_service_import_in_both_clean_process_orders():
    orders = (
        "from interface.backend.adapters.postgres_chat import PostgreSqlChatExecutor\nfrom interface.backend.chat.service import ChatService",
        "from interface.backend.chat.service import ChatService\nfrom interface.backend.adapters.postgres_chat import PostgreSqlChatExecutor",
    )
    for code in orders:
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_importing_adapter_does_not_connect_or_require_postgres():
    result = subprocess.run(
        [sys.executable, "-c", "from interface.backend.adapters.postgres_chat import PostgreSqlChatExecutor; PostgreSqlChatExecutor()"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
