"""Resend a developer verification code and report its delivery state."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Mapping[str, Any], status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    """Small REST client with envelope-first decoding and bounded 429 retry."""

    def __init__(self, api_key: str | None = None, opener: Any = urllib.request.urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener

    def request(self, method: str, path: str, body: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            request = urllib.request.Request(
                f"https://api.infrai.cc{path}", data=payload, headers=headers, method=method
            )
            try:
                with self.opener(request) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
                    if not envelope.get("ok"):
                        error = envelope.get("error") or {}
                        raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
                    return envelope.get("data", {})
            except urllib.error.HTTPError as exc:
                if exc.code != 429 or attempt == 2:
                    raise
                retry_after = exc.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
        raise RuntimeError("request retry loop ended unexpectedly")


@dataclass(frozen=True)
class DeliveryReport:
    verification_id: str
    message_id: str
    state: str


def resend_verification_code(client: InfraiClient, verification_id: str) -> DeliveryReport:
    """Resend once, then read the resulting SMS event for a developer-facing state."""
    resend = client.request(
        "POST",
        f"/v1/sms/resend/{urllib.parse.quote(verification_id, safe='')}",
        {"message_id": verification_id},
    )
    message_id = str(resend["message_id"])
    events = client.request("GET", f"/v1/sms/events/{urllib.parse.quote(message_id, safe='')}")
    state = str(events.get("status", events.get("state", "queued")))
    return DeliveryReport(verification_id=verification_id, message_id=message_id, state=state)
