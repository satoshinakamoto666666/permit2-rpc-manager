import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "task_14_solana_telegram_alert_bot"))
from solana_telegram_bot import SolanaTelegramAlertBot
from open_task_watcher import OpenTaskListingWatcher


def test_solana_telegram_alert_deduplication():
    bot = SolanaTelegramAlertBot()
    batch = [{"signature": "5abc123", "slot": 100, "err": None, "memo": "Payment #1"}]
    alerts_1 = bot.poll_new_events(batch)
    assert len(alerts_1) == 1
    assert "5abc123" in alerts_1[0]
    alerts_2 = bot.poll_new_events(batch)
    assert len(alerts_2) == 0


def test_open_task_watcher_sqlite_dedup():
    watcher = OpenTaskListingWatcher(":memory:")
    sample = [{"id": "task_1", "title": "Build parser"}, {"id": "task_2", "title": "Write spec"}]
    first = watcher.filter_new_listings(sample)
    assert len(first) == 2
    second = watcher.filter_new_listings(sample + [{"id": "task_3", "title": "New task"}])
    assert len(second) == 1
    assert second[0]["id"] == "task_3"
