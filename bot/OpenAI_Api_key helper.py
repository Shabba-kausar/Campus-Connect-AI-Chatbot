import os
from typing import Optional
from .openai_helper import get_bot_reply


# New: prefer OPENAI as the provider name and read key from OPENAI_API_KEY env var.
# This keeps compatibility if other parts of the code still reference the older name:
DEFAULT_AI_PROVIDER = os.environ.get('AI_PROVIDER', 'openai')


def get_openai_api_key() -> Optional[str]:
    """Return the OpenAI API key read from the environment.

    Looks for the following environment variables in order and returns the first found:
    - OPENAI_API_KEY
    - OPENAI_KEY

    Returns None if no key is found.
    """
    return os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')


# Backwards-compat helper: if code previously expected a variable named for Gemini/Gemeini,
# provide it but point to the OpenAI key. This avoids breaking callers while implementing
# the requested replacement.
GEMEINI_API_KEY = get_openai_api_key()  # kept for compatibility, but sourced from OPENAI_* env


def get_enhanced_response(user_query: str, context: Optional[str] = None) -> str:
    """Delegate to the centralized helper to avoid direct openai.ChatCompletion usage.

    This keeps all OpenAI interactions in `bot/openai_helper.py` so the project
    only needs to be migrated in a single place when the OpenAI client API changes.
    """
    try:
        # Reuse the project's helper that already enforces the heading+bullet format
        return get_bot_reply(user_query, context=context)
    except Exception as e:
        print(f"Error delegating to get_bot_reply: {e}")
        return "I'm having trouble processing your request. Please try again later."


def is_query_suitable_for_openai(query: str) -> bool:
    """
    Determine if a query should be handled by OpenAI model
    """
    complex_keywords = [
        'explain', 'how', 'why', 'what is', 'could you', 'difference',
        'compare', 'help me', 'understand', 'tell me about', 'describe'
    ]
    query = query.lower()
    return any(keyword in query for keyword in complex_keywords)
