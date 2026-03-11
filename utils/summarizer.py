import os
from typing import Optional

# Import the existing helper so we reuse API key handling and robust invocation
from bot.openai_helper import get_bot_reply

# Wrapper that uses get_bot_reply to summarize a content chunk with a query
# Returns either a structured reply (heading + bullets) or an error string

def summarize_with_gpt(content: str, query: str, max_tokens: int = 400) -> str:
    """Summarize content with emphasis on extracting only relevant, important information.
    
    Filters out navigation, menus, headers, footers, and repetitive content.
    Focuses on answering the user's specific query.
    """
    try:
        # Enhanced prompt to emphasize extraction of only relevant content
        enhanced_query = (
            f"User Question: {query}\n\n"
            "IMPORTANT: Extract ONLY the important and relevant information that directly answers the question. "
            "IGNORE the following:\n"
            "- Navigation menus, headers, footers\n"
            "- Repetitive text, labels, or links\n"
            "- Generic website structure elements\n"
            "- Contact information unless specifically asked\n"
            "- Footer text, copyright notices, disclaimers\n\n"
            "Focus on:\n"
            "- Specific facts, details, and information\n"
            "- Names, titles, qualifications, achievements\n"
            "- Program details, course information\n"
            "- Dates, deadlines, schedules (if relevant)\n"
            "- Any content that directly addresses the user's question\n\n"
            f"Website Content:\n{content}"
        )
        
        # Use the same get_bot_reply helper which enforces our structured format
        return get_bot_reply(enhanced_query, context=content, max_tokens=max_tokens)
    except Exception as e:
        return f"[summarizer error] {e}"
