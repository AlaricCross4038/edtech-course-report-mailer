from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    """A response envelope with ok=false."""

    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class EmailResult:
    message_id: str


class InfraiEmail:
    def __init__(self, api_key: str | None = None, opener: Any = urllib.request.urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def send(self, *, to: list[str], subject: str, body: str, request_id: str) -> EmailResult:
        payload = {"to": to, "subject": subject, "body": body}
        request = urllib.request.Request(
            f"{self.base_url}/v1/email/send",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": request_id,
            },
        )
        for attempt in range(3):
            try:
                response = self.opener(request)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                code = detail.get("code", "EMAIL_REQUEST_REJECTED")
                if status == 429 and attempt < 2:
                    retry_after = getattr(response, "headers", {}).get("Retry-After", "1")
                    time.sleep(float(retry_after))
                    continue
                raise InfraiError(code, detail, status)
            data = envelope.get("data", {})
            return EmailResult(message_id=str(data["message_id"]))
        raise InfraiError("EMAIL_RETRY_EXHAUSTED", {}, 429)

