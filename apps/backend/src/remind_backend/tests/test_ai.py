"""Tests for AI suggestion module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from remind_backend.ai import calculate_cost, suggest_reminder
from remind_backend.models import PriorityLevel


def test_calculate_cost():
    """Test cost calculation for tokens."""
    cost = calculate_cost(100, 50)
    assert cost >= 1  # Minimum 1 cent


def test_calculate_cost_large_tokens():
    """Test cost calculation with large token counts."""
    cost = calculate_cost(10000, 5000)
    assert cost >= 1


@pytest.mark.asyncio
@patch("remind_backend.ai.AsyncGroq")
@patch("remind_backend.ai.get_settings")
async def test_suggest_reminder_success(mock_settings, mock_groq_class):
    """Test successful AI suggestion."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.groq_api_key = "gsk-test"
    mock_settings_obj.ai_model = "gpt-oss-20b"
    mock_settings.return_value = mock_settings_obj

    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"suggested_text": "Call mom tomorrow", "priority": "high", "due_time_suggestion": "tomorrow 3pm"}'
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 20

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await suggest_reminder("call mom")

    assert result["suggested_text"] == "Call mom tomorrow"
    assert result["priority"] == PriorityLevel.HIGH
    assert result["due_time_suggestion"] == "tomorrow 3pm"
    assert result["cost_cents"] >= 1
    assert result["input_tokens"] == 50
    assert result["output_tokens"] == 20


@pytest.mark.asyncio
@patch("remind_backend.ai.AsyncGroq")
@patch("remind_backend.ai.get_settings")
async def test_suggest_reminder_with_null_due_time(mock_settings, mock_groq_class):
    """Test AI suggestion with null due time."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.groq_api_key = "gsk-test"
    mock_settings_obj.ai_model = "gpt-oss-20b"
    mock_settings.return_value = mock_settings_obj

    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"suggested_text": "Buy milk", "priority": "medium", "due_time_suggestion": null}'
    mock_response.usage.prompt_tokens = 40
    mock_response.usage.completion_tokens = 15

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await suggest_reminder("buy milk")

    assert result["suggested_text"] == "Buy milk"
    assert result["priority"] == PriorityLevel.MEDIUM
    assert result["due_time_suggestion"] is None


@pytest.mark.asyncio
@patch("remind_backend.ai.AsyncGroq")
@patch("remind_backend.ai.get_settings")
async def test_suggest_reminder_invalid_response(mock_settings, mock_groq_class):
    """Test handling of invalid AI response."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.groq_api_key = "gsk-test"
    mock_settings_obj.ai_model = "gpt-oss-20b"
    mock_settings.return_value = mock_settings_obj

    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "invalid json"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with pytest.raises(ValueError, match="parse AI response"):
        await suggest_reminder("test reminder")
