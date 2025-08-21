import google.generativeai as genai
from typing import Optional

# Configure the Gemini API
GEMINI_API_KEY = "AIzaSyC6gOxwWLT2froUzKBgilY0nJEEuV2gCqA"
genai.configure(api_key=GEMINI_API_KEY)

# Set up the model
model = genai.GenerativeModel('gemini-1.5-flash')

def get_enhanced_response(user_query: str, context: Optional[str] = None) -> str:
    """
    Get an enhanced response using Gemini API
    
    Args:
        user_query (str): The user's question
        context (str, optional): Any additional context from the database
        
    Returns:
        str: Enhanced response from Gemini
    """
    try:
        # Create a prompt that includes both the query and any context
        prompt = f"""You are a helpful college AI assistant. Please provide a detailed and accurate response to the following query about our college.
        
        User Query: {user_query}
        
        {f'Additional Context: {context}' if context else ''}
        
        Please provide a response that is:
        1. Informative and detailed
        2. Professional and courteous
        3. Relevant to a college setting
        4. Helpful for students or visitors
        
        Response:"""

        # Generate response
        response = model.generate_content(prompt)
        
        # Extract and clean the response
        if response and response.text:
            return response.text.strip()
        
        return "I apologize, but I couldn't generate a proper response at the moment. Please try asking your question in a different way."
        
    except Exception as e:
        print(f"Error in Gemini API call: {str(e)}")
        return "I apologize, but I'm having trouble processing your request at the moment. Please try again later."

def is_query_suitable_for_gemini(query: str) -> bool:
    """
    Determine if a query should be handled by Gemini
    
    Args:
        query (str): The user's question
        
    Returns:
        bool: Whether Gemini should handle this query
    """
    # List of keywords that suggest the query needs a more detailed or nuanced response
    complex_keywords = [
        'explain', 'how', 'why', 'what is', 'could you', 'difference',
        'compare', 'help me', 'understand', 'tell me about', 'describe'
    ]
    
    query = query.lower()
    return any(keyword in query for keyword in complex_keywords) 