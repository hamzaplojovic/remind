"""AI service for reminder suggestions."""

from remind_shared import AIResponse, PriorityLevel


class AIService:
    """Service for AI-powered reminder suggestions."""

    def __init__(self, backend_url: str | None = None, openai_key: str | None = None):
        """Initialize AI service.

        Args:
            backend_url: URL to Remind backend API (production)
            openai_key: OpenAI API key for local usage
        """
        self.backend_url = backend_url
        self.openai_key = openai_key

    def suggest_reminder(self, text: str) -> AIResponse:
        """Get AI suggestion for reminder text.

        Args:
            text: Original reminder text

        Returns:
            AIResponse with suggested text, priority, and timing
        """
        if self.backend_url:
            return self._suggest_via_backend(text)
        elif self.openai_key:
            return self._suggest_via_openai(text)
        else:
            # No AI configured - return as-is
            return AIResponse(
                suggested_text=text,
                priority=PriorityLevel.MEDIUM,
            )

    def _suggest_via_backend(self, text: str) -> AIResponse:
        """Get suggestion from Remind backend API."""
        # TODO: Implement backend API call
        raise NotImplementedError("Backend API calls not yet implemented")

    def _suggest_via_openai(self, text: str) -> AIResponse:
        """Get suggestion from OpenAI directly."""
        # TODO: Implement OpenAI API call
        raise NotImplementedError("OpenAI API calls not yet implemented")
