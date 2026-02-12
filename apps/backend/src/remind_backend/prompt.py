"""AI prompt templates."""


def build_suggestion_prompt(reminder_text: str) -> str:
    """Build the prompt for AI reminder suggestion."""
    return f"""You are a helpful reminder assistant. The user has entered a reminder: "{reminder_text}"

Your task:
1. Rephrase it to be clear and concise
2. Determine priority (low, medium, high) based on urgency/importance
3. If a time is mentioned, extract due_time_suggestion, otherwise null

Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "suggested_text": "Clear rephrased reminder",
  "priority": "low|medium|high",
  "due_time_suggestion": "time or null"
}}"""
