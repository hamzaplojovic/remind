"""AI integration with Groq."""

import json
from typing import TypedDict

from groq import AsyncGroq

from remind_backend.config import get_settings
from remind_backend.models import PriorityLevel
from remind_backend.prompt import build_suggestion_prompt


class AIResponse(TypedDict):
    """AI suggestion response."""

    suggested_text: str
    priority: PriorityLevel
    due_time_suggestion: str | None
    cost_cents: int
    input_tokens: int
    output_tokens: int


def calculate_cost(input_tokens: int, output_tokens: int) -> int:
    """Calculate cost in cents for Groq gpt-oss-20b.

    Groq gpt-oss-20b pricing (as of 2025):
    - Input: $0.00001 per 1K tokens (extremely cheap)
    - Output: $0.00002 per 1K tokens
    """
    input_cost = (input_tokens / 1000) * 0.00001
    output_cost = (output_tokens / 1000) * 0.00002
    total_cents = int((input_cost + output_cost) * 100)
    return max(1, total_cents)  # Minimum 1 cent per request


async def suggest_reminder(reminder_text: str) -> AIResponse:
    """Get AI suggestion for reminder text using Groq."""
    settings = get_settings()
    client = AsyncGroq(api_key=settings.groq_api_key)

    prompt = build_suggestion_prompt(reminder_text)

    response = await client.chat.completions.create(
        model=settings.ai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    # Parse response
    try:
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from AI")
        data = json.loads(content.strip())
    except (json.JSONDecodeError, KeyError, IndexError, AttributeError) as e:
        raise ValueError(f"Failed to parse AI response: {e}")

    # Extract token usage
    if not response.usage:
        raise ValueError("No usage data in response")
    input_tokens = response.usage.prompt_tokens or 0
    output_tokens = response.usage.completion_tokens or 0
    cost_cents = calculate_cost(input_tokens, output_tokens)

    return AIResponse(
        suggested_text=data.get("suggested_text", reminder_text),
        priority=PriorityLevel(data.get("priority", "medium")),
        due_time_suggestion=data.get("due_time_suggestion"),
        cost_cents=cost_cents,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
