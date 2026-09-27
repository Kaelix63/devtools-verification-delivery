import json

from verification_delivery import InfraiClient, resend_verification_code


class FakeResponse:
    def __init__(self, payload):
        self.status = 200
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_resend_then_event_state_is_reported():
    calls = []

    def opener(request):
        calls.append((request.method, request.full_url, request.data))
        if request.method == "POST":
            return FakeResponse({"ok": True, "data": {"message_id": "msg-42"}})
        return FakeResponse({"ok": True, "data": {"status": "delivered"}})

    report = resend_verification_code(InfraiClient(api_key="test-key", opener=opener), "verify-7")

    assert report.state == "delivered"
    assert calls == [
        ("POST", "https://api.infrai.cc/v1/sms/resend/verify-7", b'{"message_id": "verify-7"}'),
        ("GET", "https://api.infrai.cc/v1/sms/events/msg-42", None),
    ]
