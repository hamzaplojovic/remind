"""AI service for reminder suggestions."""

import httpx

from remind_shared import AIResponse, PriorityLevel
from remind_cli.config import load_config
from remind_cli.services.config_service import ConfigService


class AIService:
    """Service for AI-powered reminder suggestions."""

    def __init__(self, backend_url: str | None = None, openai_key: str | None = None):
        self.backend_url = backend_url
        self.openai_key = openai_key

    def suggest_reminder(self, text: str) -> AIResponse:
        """Get AI suggestion for reminder text."""
        backend_url = self.backend_url or self._get_configured_backend_url()
        openai_key = self.openai_key or self._get_configured_openai_key()

        if backend_url:
            return self._suggest_via_backend(text, backend_url)
        elif openai_key:
            return self._suggest_via_openai(text, openai_key)
        else:
            return AIResponse(
                suggested_text=text,
                priority=PriorityLevel.MEDIUM,
                quota_exhausted=False,
            )

    def _get_configured_backend_url(self) -> str | None:
        try:
            config = load_config()
            return config.ai_backend_url
        except Exception:
            return None

    def _get_configured_openai_key(self) -> str | None:
        try:
            config = load_config()
            return config.openai_api_key
        except Exception:
            return None

    def _suggest_via_backend(self, text: str, backend_url: str) -> AIResponse:
        """Get suggestion from Remind backend API."""
        try:
            config_service = ConfigService()
            license_token = config_service.get_license_token()
            if not license_token:
                return AIResponse(
                    suggested_text=text,
                    priority=PriorityLevel.MEDIUM,
                )

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{backend_url.rstrip('/')}/api/v1/suggest-reminder",
                    json={"license_token": license_token, "reminder_text": text},
                )

                if response.status_code == 429:
                    return AIResponse(
                        suggested_text=text,
                        priority=PriorityLevel.MEDIUM,
                        quota_exhausted=True,
                    )
                elif response.status_code != 200:
                    return AIResponse(
                        suggested_text=text,
                        priority=PriorityLevel.MEDIUM,
                    )

                data = response.json()
                return AIResponse(
                    suggested_text=data.get("suggested_text", text),
                    priority=PriorityLevel(data.get("priority", "medium")),
                    due_time_suggestion=data.get("due_time_suggestion"),
                    cost_estimate=data.get("cost_cents", 0) / 100.0 if data.get("cost_cents") else None,
                )
        except Exception:
            return AIResponse(
                suggested_text=text,
                priority=PriorityLevel.MEDIUM,
            )

    def _suggest_via_openai(self, text: str, openai_key: str) -> AIResponse:
        """Get suggestion from OpenAI directly."""
        return AIResponse(
            suggested_text=text,
            priority=PriorityLevel.MEDIUM,
        )
