import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notification_dispatcher import NotificationDispatcher


def test_notification_dispatcher_all_four_events():
    sent_emails = []
    dispatcher = NotificationDispatcher(mailer=lambda to, subj, body: (sent_emails.append((to, subj)), True)[1])

    dispatcher.on_bid_created("b1", "t1", "Build Parser", "owner_1", "bot_1", "100 USDC")
    dispatcher.on_contract_hired("c1", "Build Parser", "seller_1", "owner_1")
    dispatcher.on_deliverable_submitted("d1", "c1", "Build Parser", "owner_1", "seller_1")
    dispatcher.on_contract_closed("c1", "Build Parser", "seller_1", "owner_1")

    owner_notifs = dispatcher.list_notifications("owner_1")
    seller_notifs = dispatcher.list_notifications("seller_1")
    assert len(owner_notifs) == 3
    assert len(seller_notifs) == 2
    assert len(sent_emails) == 5
