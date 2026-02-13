"""Email service for sending license tokens to customers via Resend."""

import logging

import httpx

from remind_backend.config import get_settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def send_license_email(to_email: str, token: str, plan_tier: str) -> bool:
    """Send license token to customer via Resend. Returns True on success."""
    settings = get_settings()

    if not settings.resend_api_key:
        logger.warning("Resend API key not configured — printing token to console instead")
        logger.info("LICENSE TOKEN for %s (%s): %s", to_email, plan_tier, token)
        return True

    html_body = f"""\
<html>
<body style="font-family: 'Manrope', system-ui, sans-serif; color: #1a1715; max-width: 560px; margin: 0 auto; padding: 40px 20px;">
  <h1 style="font-family: Georgia, serif; font-size: 28px; margin-bottom: 8px;">
    remind<span style="color: #e8503a;">.</span>
  </h1>
  <p style="color: #6b645c; margin-bottom: 32px;">AI-Powered Reminder CLI</p>
  <hr style="border: none; height: 1px; background: #d4cfc7; margin-bottom: 32px;">

  <p>Welcome to Remind <strong>{plan_tier.capitalize()}</strong>!</p>
  <p>Here is your license token:</p>

  <div style="background: #1a1715; color: #f0ebe4; padding: 16px 20px; font-family: monospace; font-size: 14px; margin: 24px 0; border-radius: 6px;">
    {token}
  </div>

  <p>To activate, run this in your terminal:</p>
  <div style="background: #1a1715; color: #f0ebe4; padding: 16px 20px; font-family: monospace; font-size: 14px; margin: 24px 0; border-radius: 6px;">
    <span style="color: #52b788;">$</span> remind login {token}
  </div>

  <hr style="border: none; height: 1px; background: #d4cfc7; margin: 32px 0;">
  <p style="color: #b0a99e; font-size: 13px;">
    Keep this token safe — it's your license key. If you lose it, contact us and we'll reissue it.
  </p>
</body>
</html>"""

    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.email_from,
                "to": [to_email],
                "subject": f"Your Remind {plan_tier.capitalize()} License",
                "html": html_body,
            },
            timeout=10,
        )
        if response.status_code == 200:
            logger.info("License email sent to %s via Resend", to_email)
            return True
        else:
            logger.error("Resend API error %d: %s", response.status_code, response.text)
            return False
    except Exception:
        logger.exception("Failed to send license email to %s", to_email)
        return False
