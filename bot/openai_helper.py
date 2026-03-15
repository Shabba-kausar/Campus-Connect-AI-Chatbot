import os
# Load .env automatically if present so developers can set OPENAI_API_KEY there
try:
    from dotenv import load_dotenv
    # Do not override existing environment variables; load only if not set
    load_dotenv(override=False)
except Exception:
    # dotenv is optional; if it's not installed or fails, we'll rely on os.environ
    pass
from typing import Optional

# Import OpenAI lazily; allow the project to import even if the package
# isn't installed so Django can start. get_enhanced_response will return
# a clear error if the package is missing.
try:
    from openai import OpenAI
except Exception:
    OpenAI = None
    # If developer enabled debug, include the python executable in error messages
    import os as _os
    _DEBUG_OPENAI_IMPORT = _os.getenv('DEBUG_OPENAI_IMPORT', '0') == '1'
    if _DEBUG_OPENAI_IMPORT:
        try:
            import sys as _sys
            # Attach the executable path to environment for later use when returning errors
            _os.environ['_OPENAI_IMPORT_PYTHON_EXE'] = _sys.executable
        except Exception:
            pass


def _get_api_key() -> str:
    # Check environment first
    key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
    if not key:
        # Try reading from Django settings if this module is used within a Django app
        try:
            from django.conf import settings as dj_settings
            key = getattr(dj_settings, 'OPENAI_API_KEY', None)
        except Exception:
            key = None

    if not key:
        raise RuntimeError("OpenAI API key not set. Please set OPENAI_API_KEY in your environment or .env file.")
    return key


def is_query_suitable_for_llm(user_message: str) -> bool:
    """Legacy name kept: decides whether to call the LLM for open-ended queries.

    Simple heuristic: if message is > 3 words and not an exact quick-reply trigger,
    consider it suitable for the LLM.
    """
    if not user_message:
        return False
    words = user_message.strip().split()
    return len(words) > 3


def get_enhanced_response(prompt: str, max_tokens: int = 400) -> str:
    """Call OpenAI chat completion and return formatted content.

    Ensures the model returns a heading and bullet points. If the model reply
    doesn't match the format, we still return the content.
    """
    try:
        key = _get_api_key()
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        # Strong system instructions to enforce structured, short answers
        system_instructions = (
            "You are the MANUU Hyderabad Campus AI Chatbot, an intelligent assistant built for Maulana Azad National Urdu University (MANUU), Hyderabad.\n\n"
            "🎯 Your Core Objective:\n"
            "Provide real-time, verified, and official information only related to MANUU Hyderabad Campus, by fetching live data from the official MANUU website: https://manuu.edu.in/\n\n"
            "🔗 Authorized Data Source URLs:\n"
            "You may fetch and summarize content only from these verified Hyderabad campus links:\n"
            "- https://manuu.edu.in/\n"
            "- https://manuu.edu.in/About-MANUU\n"
            "- https://manuu.edu.in/Academics\n"
            "- https://manuu.edu.in/Schools\n"
            "- https://manuu.edu.in/Programs\n"
            "- https://manuu.edu.in/admissions\n"
            "- https://manuu.edu.in/Examination\n"
            "- https://manuu.edu.in/Hostels\n"
            "- https://manuu.edu.in/Campus-Life\n"
            "- https://manuu.edu.in/Faculty\n"
            "- https://manuu.edu.in/Events\n"
            "- https://manuu.edu.in/Contact-Us\n\n"
            "🔗 CSIT Department URLs (School of Computer Science and Information Technology):\n"
            "For CSIT-specific queries, fetch live data from these approved URLs:\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/Profile\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/People\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/People/741 (Prof. Pradeep Kumar - HOD)\n"
            "- https://manuu.edu.in/University/SCSIT/People/581 (Prof. Abdul Wahid - Dean)\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/Programs-Syllabus\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/Resources/Class-Time-Table\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/Research-Publications\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/Research-Scholars\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/major-project\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/minor-project\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/Facilities\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/notifications\n"
            "- https://manuu.edu.in/University/SCSIT/CSIT/TP-cell\n"
            "- https://manuu.edu.in/University/School/SCSIT/ContactUs\n\n"
            "🧠 Rules:\n"
            "- Restrict responses to Hyderabad campus only.\n"
            "- Always provide the official URL reference used in your answer.\n"
            "- For CSIT queries: Extract important and relevant text, ignore menus/headers/repetitive sections. Summarize clearly.\n"
            "- For CSIT queries: Include a '📎 Official Sources:' section listing all URLs used.\n"
            "- If a query cannot be answered, respond with: 'Please visit https://manuu.edu.in/ for the most updated information.'\n"
            "- For CSIT queries with no info found: 'I couldn't find updated details on the official MANUU CSIT site. Please visit https://manuu.edu.in/University/SCSIT/CSIT for more information.'\n"
            "- For queries about exam date, midterm, internal, etc. → respond: 'Please contact the MANUU Examination Cell for accurate updates.'\n"
            "- Do not answer from memory or static data — always rely on live website content.\n\n"
            "💬 Response Style:\n"
            "- Clear, short, and factual.\n"
            "- Only use current live data.\n"
            "- Never include information from other MANUU campuses.\n"
            "- Start with a single short heading (one line). Markdown bold is OK (e.g., **CSIT Department - Faculty**).\n"
            "- Immediately below the heading provide 2-5 short bullet points (each on its own line, starting with '-', '*', or a number).\n"
            "- Do NOT write long paragraphs, do NOT add extra commentary, and do NOT ask the user to clarify.\n"
            "- For CSIT responses, include '📎 Official Sources:' section with URLs at the end.\n"
            "- If a relevant link exists, append exactly one final line starting with '➡️ For more information, visit: ' followed by the link.\n"
            "Always follow this format strictly."
        )

        # Compose messages once
        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": prompt},
        ]

        resp = None
        # Try several possible invocation patterns because different openai package
        # versions expose slightly different APIs (client.chat.create vs client.chat.completions.create
        # vs openai.ChatCompletion.create). Try them in order and fall back gracefully.
        # 1) Try the modern OpenAI client if available (OpenAI class)
        if OpenAI is not None:
            try:
                client = OpenAI(api_key=key)
                # Many OpenAI client releases expose slightly different chat APIs.
                # Try the most common / modern ones in order and capture helpful
                # debug messages when a given attribute is missing.
                try:
                    # Newer SDKs: client.chat.completions.create(...)
                    if hasattr(client, 'chat') and hasattr(client.chat, 'completions') and hasattr(client.chat.completions, 'create'):
                        resp = client.chat.completions.create(
                            model=model, messages=messages, temperature=0.2, max_tokens=max_tokens
                        )
                    # Older variant: client.chat.create(...)
                    elif hasattr(client, 'chat') and hasattr(client.chat, 'create'):
                        resp = client.chat.create(
                            model=model, messages=messages, temperature=0.2, max_tokens=max_tokens
                        )
                    else:
                        # If the client shape is unexpected, raise to fall back to the classic module interface
                        raise AttributeError("OpenAI client 'chat' API has unexpected attributes: " + str([a for a in dir(client.chat) if not a.startswith('_')]) if hasattr(client, 'chat') else 'no chat attr')
                except Exception as inner_e:
                    # Keep inner exception message for easier debugging in logs
                    last_inner_err = str(inner_e)
                    resp = None
            except Exception as e:
                last_inner_err = str(e)
                resp = None

        # 2) Fallback to the installed openai module. Prefer the modern OpenAI
        # client (openai.OpenAI) if available. Avoid using the removed
        # openai.ChatCompletion interface (no longer present in openai>=1.0.0).
        if resp is None:
            try:
                import openai as openai_module
                # If the module exposes the modern OpenAI client, use it
                if hasattr(openai_module, 'OpenAI'):
                    try:
                        client_mod = openai_module.OpenAI(api_key=key)
                        if hasattr(client_mod, 'chat') and hasattr(client_mod.chat, 'completions') and hasattr(client_mod.chat.completions, 'create'):
                            resp = client_mod.chat.completions.create(
                                model=model, messages=messages, temperature=0.2, max_tokens=max_tokens
                            )
                        elif hasattr(client_mod, 'chat') and hasattr(client_mod.chat, 'create'):
                            # Some variants expose chat.create
                            resp = client_mod.chat.create(
                                model=model, messages=messages, temperature=0.2, max_tokens=max_tokens
                            )
                        else:
                            # Unexpected client shape
                            raise AttributeError('Installed openai client does not expose a supported chat API')
                    except Exception as inner_e:
                        raise inner_e
                else:
                    # Very old openai versions may have ChatCompletion; do not attempt
                    # to call deprecated interfaces here — instruct user to upgrade
                    return ("[LLM error] Installed 'openai' package does not provide the modern OpenAI client. "
                            "Please upgrade to the latest 'openai' package (pip install -U openai) and ensure your code uses the OpenAI client API.")
            except Exception as e:
                # Return a helpful message to guide debug/upgrade of the openai package
                return f"[LLM error] Could not call OpenAI API: {str(e)}. \nPlease ensure the 'openai' Python package is installed and up-to-date (pip install -U openai)."

        # Robust content extraction supporting dict-like or object responses
        content = ''
        try:
            # resp may be dict-like or an object with attributes
            choices = None
            if hasattr(resp, 'choices'):
                choices = resp.choices
            elif isinstance(resp, dict):
                choices = resp.get('choices', [])
            elif hasattr(resp, 'get'):
                # try generic get
                choices = resp.get('choices', [])

            if choices:
                choice = choices[0]
                # message may be a dict or object
                message = None
                if isinstance(choice, dict):
                    message = choice.get('message') or choice.get('delta')
                else:
                    message = getattr(choice, 'message', None) or getattr(choice, 'delta', None)

                if isinstance(message, dict):
                    content = message.get('content', '') or message.get('text', '')
                else:
                    content = getattr(message, 'content', '') if message is not None else ''

                # Some responses put the text directly on the choice
                if not content:
                    if isinstance(choice, dict):
                        content = choice.get('text', '') or choice.get('message', {}).get('content', '')
                    else:
                        content = getattr(choice, 'text', '') or ''
        except Exception:
            content = ''

        return (content or '').strip()
    except Exception as e:
        return f"[LLM error] {str(e)}"


def get_bot_reply(user_query: str, context: Optional[str] = "", max_tokens: int = 400) -> str:
    """Higher-level helper that enforces our policy:

    - If no context is provided, return a clear fallback string immediately (no LLM call).
    - If context is provided, call get_enhanced_response() with a compact user prompt that
      includes the user question and the website/context text.

    Returns the model's reply (which should be a heading + 2-5 bullets) or an error string
    that starts with '[LLM error]'.
    """
    try:
        # Development/mock mode: ONLY check the explicit env var.
        mock_env = os.getenv('MOCK_OPENAI', '0').lower() in ('1', 'true', 'yes')
        if mock_env:
            print('[openai_helper] MOCK_OPENAI enabled via environment variable')
        if mock_env:
            q = (user_query or '').lower()
            # Simple canned map — expand as needed
            if 'hostel' in q:
                return "**Hostel Details (Hyderabad Campus)**\n- Separate hostels for boys and girls\n- Rooms with basic furnishings and shared mess\n- 24x7 security and electricity\n➡️ For more information, visit: https://manuu.edu.in/Hostels"
            if 'admission' in q or 'admit' in q:
                return "**Admission Process (Hyderabad Campus)**\n- Apply online through the official portal\n- Submit documents for verification\n- Selection based on entrance/merit as applicable\n➡️ For more information, visit: https://manuu.edu.in/admissions"
            if 'course' in q or 'courses' in q:
                return "**Courses Overview**\n- UG, PG, and PhD programs across Arts, Science, Technology\n- Professional and vocational certificate programs\n- Check department pages for syllabus details\n➡️ For more information, visit: https://manuu.edu.in/Programs"
            # default mock fallback
            return "Please visit https://manuu.edu.in/ for the most updated information."

        if not context or not str(context).strip():
            # Explicit, strict fallback when no data is available - use exact message from requirements
            return "Please visit https://manuu.edu.in/ for the most updated information."

        # Build a compact prompt for the user + context. The system prompt in
        # get_enhanced_response() already enforces the format, so we only pass
        # user-visible content here.
        prompt = f"User Question: {user_query}\n\nWebsite Data: {context}"
        reply = get_enhanced_response(prompt, max_tokens=max_tokens)
        
        # Intercept LLM Error explicitly and rewrite it to a visually appealing UI message
        if reply.startswith("[LLM error]"):
            if "429" in reply or "quota" in reply.lower() or "insufficient_quota" in reply.lower():
                return ("[QUOTA_EXCEEDED] **⚠️ Temporary AI Limitations**\n"
                        "Our background AI summarization service has temporarily reached its billing quota. "
                        "The system successfully found the information from MANUU's official website, but cannot summarize it right now. "
                        "\n\n*Please try again later or consult the provided official links directly!*")
            return f"**⚠️ AI Service Error:**\nAn unexpected error occurred while generating the response. Please try again later."
            
        return reply
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "quota" in err_str.lower():
            return ("[QUOTA_EXCEEDED] **⚠️ Temporary AI Limitations**\n"
                    "Our AI summarization service has temporarily reached its quota limits. "
                    "However, the source links below have still been fetched for your convenience!")
        return f"**⚠️ Error:** {err_str}"
