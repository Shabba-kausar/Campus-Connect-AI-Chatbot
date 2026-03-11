import os
from typing import Optional


def get_openai_api_key() -> Optional[str]:
    """Return the OpenAI API key read from the environment.

    Looks for OPENAI_API_KEY or OPENAI_KEY.
    """
    return os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')


def ensure_openai_key():
    key = get_openai_api_key()
    if not key:
        raise RuntimeError('OPENAI_API_KEY missing; set it in your .env or environment')
    return key
