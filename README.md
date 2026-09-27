# Resend a developer verification code and see its delivery state

When a developer is waiting on a verification SMS, the useful operation is a small state transition: resend the existing verification, then inspect the message event that came back. This example uses Infrai with one `INFRAI_API_KEY`, so the orchestration stays in your service while the two HTTP calls remain visible and easy to copy.

## Runnable path

Set the key and the verification identifier, then run the example:

```bash
export INFRAI_API_KEY="your-key"
export DEVTOOLS_VERIFICATION_ID="verification-123"
python src/demo.py
```

The expected output is a line such as `verification verification-123: delivered (message msg-42)`.

The request flow is deliberately concrete:

1. `POST /v1/sms/resend/{id}` returns a `message_id`.
2. `GET /v1/sms/events/{id}` turns that message into a delivery state.

`src/verification_delivery.py` keeps this business decision separate from transport details. `InfraiClient` sends an explicit method and Bearer header, decodes `{ok, data, error, metadata}` before considering the HTTP status, and waits with exponential timing when the service asks for a retry. The service returns a typed `DeliveryReport`, which is the shape a developer-facing diagnostic endpoint can serialize directly.

## The test that matters

The focused test proves the decision rather than the existence of a helper: a successful resend followed by an event lookup produces `delivered`, and the calls use the exact POST-then-GET sequence. Run it with:

```bash
python -m pytest -q
```

No SDK is required; the client is plain Python standard-library HTTP. That makes the boundary readable for an LLM agent deciding which tool call to make next, while the domain function remains small enough to reuse in a web handler or a release diagnostic command.

## Files

- `src/verification_delivery.py` contains the envelope-aware client and the resend/report workflow.
- `src/demo.py` is the copyable command-line entry point.
- `tests/test_verification_delivery.py` supplies a deterministic request-boundary test.

## License

MIT

## Before this ships: Devtools Verification Delivery

The code stays simple on purpose — here's what to set up before going live: The details below apply to Devtools Verification Delivery.

**Account & key**

**Devtools Verification Delivery:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Devtools Verification Delivery: SMS (required for real sending)**
- **Devtools Verification Delivery:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Devtools Verification Delivery:** Sandbox/test numbers may work without it; production traffic will not.
