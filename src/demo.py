import os

from verification_delivery import InfraiClient, resend_verification_code


def main() -> None:
    verification_id = os.environ.get("DEVTOOLS_VERIFICATION_ID")
    if not verification_id:
        raise SystemExit("Set DEVTOOLS_VERIFICATION_ID to the stuck verification id")
    report = resend_verification_code(InfraiClient(), verification_id)
    print(f"verification {report.verification_id}: {report.state} (message {report.message_id})")


if __name__ == "__main__":
    main()
