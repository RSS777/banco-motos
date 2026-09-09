from types import SimpleNamespace

import pytest
from pywebpush import WebPushException

from pipeline.models import RunSummary
from pipeline.notifiers.web_push_notifier import WebPushNotifier


class _FakeQuery:
    def __init__(self, table, op, **kwargs):
        self._table = table
        self._op = op
        self._kwargs = kwargs

    def eq(self, field, value):
        self._kwargs["eq"] = (field, value)
        return self

    def execute(self):
        if self._op == "select":
            return SimpleNamespace(data=list(self._table.rows))
        if self._op == "delete":
            field, value = self._kwargs["eq"]
            self._table.rows = [r for r in self._table.rows if r[field] != value]
            return SimpleNamespace(data=[])
        raise AssertionError(f"unexpected op {self._op}")


class _FakeTable:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args):
        return _FakeQuery(self, "select")

    def delete(self):
        return _FakeQuery(self, "delete")


class _FakeSupabaseClient:
    def __init__(self, rows):
        self._table = _FakeTable(rows)

    def table(self, name):
        assert name == "push_subscriptions"
        return self._table


SUB_A = {"id": "1", "endpoint": "https://push.example/a", "p256dh": "pA", "auth": "aA"}
SUB_B = {"id": "2", "endpoint": "https://push.example/b", "p256dh": "pB", "auth": "aB"}
SUMMARY = RunSummary(candidates_seen=5, processed=3, failed=1, skipped=1)


def test_sends_to_every_stored_subscription(monkeypatch):
    import pipeline.notifiers.web_push_notifier as module

    sent = []
    monkeypatch.setattr(
        module, "webpush", lambda **kwargs: sent.append(kwargs["subscription_info"]["endpoint"])
    )

    client = _FakeSupabaseClient([SUB_A, SUB_B])
    notifier = WebPushNotifier(client=client, vapid_private_key="k", vapid_subject="mailto:x@y.com")

    notifier.notify(SUMMARY)

    assert sent == [SUB_A["endpoint"], SUB_B["endpoint"]]


def test_gone_subscription_is_removed_others_still_sent(monkeypatch):
    import pipeline.notifiers.web_push_notifier as module

    sent = []

    def fake_webpush(**kwargs):
        endpoint = kwargs["subscription_info"]["endpoint"]
        if endpoint == SUB_A["endpoint"]:
            exc = WebPushException("gone")
            exc.response = SimpleNamespace(status_code=410)
            raise exc
        sent.append(endpoint)

    monkeypatch.setattr(module, "webpush", fake_webpush)

    client = _FakeSupabaseClient([SUB_A, SUB_B])
    notifier = WebPushNotifier(client=client, vapid_private_key="k", vapid_subject="mailto:x@y.com")

    notifier.notify(SUMMARY)

    assert sent == [SUB_B["endpoint"]]
    assert client._table.rows == [SUB_B]  # SUB_A removed


def test_non_gone_failure_is_logged_not_raised_and_subscription_kept(monkeypatch):
    import pipeline.notifiers.web_push_notifier as module

    def fake_webpush(**kwargs):
        exc = WebPushException("server error")
        exc.response = SimpleNamespace(status_code=500)
        raise exc

    monkeypatch.setattr(module, "webpush", fake_webpush)

    client = _FakeSupabaseClient([SUB_A])
    notifier = WebPushNotifier(client=client, vapid_private_key="k", vapid_subject="mailto:x@y.com")

    notifier.notify(SUMMARY)  # must not raise

    assert client._table.rows == [SUB_A]  # not removed for a transient failure
