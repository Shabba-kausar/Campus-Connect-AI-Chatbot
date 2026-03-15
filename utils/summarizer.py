import os
from typing import Optional

# Import the existing helper so we reuse API key handling and robust invocation
from bot.openai_helper import get_bot_reply

# Wrapper that uses get_bot_reply to summarize a content chunk with a query
# Returns either a structured reply (heading + bullets) or an error string

def heuristic_web_parser(content: str, query: str) -> str:
    """
    Fallback parser that extracts meaningful information from structured web text 
    without using an LLM. Processes headers, bullets, and tables.
    """
    if not content:
        return "I found the page on the MANUU website, but could not extract readable details. Please check the link below."
    
    query_terms = (query or "").lower().split()
    sections = content.split('###')
    relevant_sections = []
    
    # Heuristic 1: Find sections containing query keywords
    for section in sections:
        if any(term in section.lower() for term in query_terms):
            relevant_sections.append(section.strip())
            
    # Heuristic 2: Extract List items (dots/bullets)
    lines = content.split('\n')
    bullets = [line.strip() for line in lines if line.strip().startswith('•')]
    
    # Build a structured response
    resp = "**⚠️ Note: High Traffic Fallback Active**\n"
    resp += "Our AI service is busy, but I've extracted this information directly from the official MANUU page for you:\n\n"
    
    if relevant_sections:
        # Show top 2 relevant snippets
        for i, sec in enumerate(relevant_sections[:2]):
            # Clean up the trailing ### if it exists
            clean_sec = sec.rstrip('###').strip()
            resp += f"### {clean_sec}\n\n"
    
    if bullets and len(relevant_sections) < 1:
        # If no targeted sections found, but bullets exist, show some bullets
        resp += "**Key Points Found:**\n"
        for bull in bullets[:10]:
            resp += f"{bull}\n"
        resp += "\n"
        
    if not relevant_sections and not bullets:
        # Fallback to a preview of the text
        resp += "**Information Summary:**\n"
        resp += content[:600] + "..."
        
    return resp

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
        resp = get_bot_reply(enhanced_query, context=content, max_tokens=max_tokens)
        
        # Check for our programmatic quota marker
        if resp.startswith("[QUOTA_EXCEEDED]"):
            return heuristic_web_parser(content, query)
            
        return resp
    except Exception as e:
        # If any other error occurs, try the heuristic parser as a last resort
        try:
            return heuristic_web_parser(content, query)
        except:
            return f"[summarizer error] {e}"
