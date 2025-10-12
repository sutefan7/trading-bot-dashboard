from pathlib import Path
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

psutil_stub = types.SimpleNamespace(
    cpu_percent=lambda interval=0: 5.0,
    virtual_memory=lambda: types.SimpleNamespace(percent=25.0, used=1, total=4),
    disk_usage=lambda path: types.SimpleNamespace(used=1, total=4),
    cpu_count=lambda: 4,
)
sys.modules.setdefault("psutil", psutil_stub)

import web_server


@pytest.fixture
def temp_data_dir(tmp_path):
    trades_csv = tmp_path / "trades_summary.csv"
    trades_csv.write_text(
        "timestamp,total_trades,unique_requests,chain_integrity,verified_records,total_records,winning_trades,losing_trades,win_rate\n"
        "2024-01-01T00:00:00Z,10,5,1,10,10,6,4,0.6\n",
        encoding="utf-8"
    )

    equity_csv = tmp_path / "equity.csv"
    equity_csv.write_text(
        "timestamp,balance,pnl,total_trades,winning_trades,losing_trades,win_rate\n"
        "2024-01-01T00:00:00Z,1000,50,10,6,4,0.6\n",
        encoding="utf-8"
    )

    return tmp_path


def test_trading_performance_missing_snapshot(monkeypatch, temp_data_dir):
    monkeypatch.setattr(web_server.pi_api_client, "check_pi_connectivity", lambda: True)
    monkeypatch.setattr(
        web_server.pi_api_client,
        "get_trading_performance_data",
        lambda: {"error": "missing", "data_source": "pi_snapshot"}
    )

    fallback_calls = {"needed": []}

    def fake_is_fallback_needed(pi_online):
        fallback_calls["needed"].append(pi_online)
        return False

    monkeypatch.setattr(web_server.fallback_manager, "is_fallback_needed", fake_is_fallback_needed)

    monkeypatch.setattr(
        web_server.fallback_manager,
        "get_fallback_trading_performance",
        lambda: {"error": "fallback"}
    )

    monkeypatch.setattr(web_server, "MAX_FILE_SIZE", 10 * 1024 * 1024, raising=False)
    monkeypatch.setattr(web_server, "ALLOWED_CSV_COLUMNS", web_server.Config.ALLOWED_CSV_COLUMNS, raising=False)

    data_processor = web_server.DataProcessor(temp_data_dir)
    monkeypatch.setattr(web_server, "data_processor", data_processor)

    monkeypatch.setattr(web_server.config, "AUTH_ENABLED", False, raising=False)

    client = web_server.app.test_client()
    response = client.get("/api/trading-performance")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data_source"] == "csv_local"
    assert payload["total_trades"] == 10
    assert pytest.approx(payload["win_rate"], rel=1e-6) == 0.6
    assert fallback_calls["needed"] == [True]
