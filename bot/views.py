from .gemini_helper import get_enhanced_response, is_query_suitable_for_gemini
import google.generativeai as genai
from django.conf import settings
genai.configure(api_key=settings.GEMINI_API_KEY)
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
from .models import Conversation, Message, CollegeData, Category
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .gemini_helper import get_enhanced_response, is_query_suitable_for_gemini

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def process_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            user_id = data.get('user_id', '')
            user_name = data.get('name', '')
            user_phone = data.get('phone', '')
            
            # Get or create conversation
            if user_id:
                conversation, created = Conversation.objects.get_or_create(
                    user_identifier=user_id,
                    defaults={'user_name': user_name, 'user_phone': user_phone}
                )
                if not created and (user_name or user_phone):
                    conversation.user_name = user_name or conversation.user_name
                    conversation.user_phone = user_phone or conversation.user_phone
                    conversation.save()
            else:
                conversation = Conversation.objects.create(
                    user_name=user_name,
                    user_phone=user_phone
                )
            
            # Save user message
            Message.objects.create(
                conversation=conversation,
                sender='user',
                content=user_message
            )
            
            # Generate response using combined approach
            bot_response = generate_response(user_message)
            
            # Save bot message
            Message.objects.create(
                conversation=conversation,
                sender='bot',
                content=bot_response
            )
            
            return JsonResponse({
                'message': bot_response,
                'user_id': conversation.user_identifier or str(conversation.id)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def generate_response(user_message):
    # Clean user message
    user_message = user_message.lower().strip()
    
    # Handle quick replies first
    quick_reply_response = handle_quick_reply(user_message)
    if quick_reply_response:
        return quick_reply_response

    # Check if query is suitable for Gemini
    use_gemini = is_query_suitable_for_gemini(user_message)
    
    # Try to find category-based matches first
    try:
        category = None
        for cat_name, keywords in category_keywords.items():
            if any(keyword in user_message for keyword in keywords):
                category = Category.objects.filter(name__icontains=cat_name).first()
                if category:
                    matches = CollegeData.objects.filter(category=category)
                    if matches.exists():
                        db_response = get_best_category_response(matches, user_message)
                        if use_gemini:
                            return get_enhanced_response(user_message, context=db_response)
                        return db_response
    except Exception as e:
        print(f"Category search error: {str(e)}")

    # Try exact keyword matches
    try:
        exact_matches = CollegeData.objects.filter(
            keywords__icontains=user_message
        )
        if exact_matches.exists():
            db_response = random.choice(list(exact_matches)).answer
            if use_gemini:
                return get_enhanced_response(user_message, context=db_response)
            return db_response
    except Exception as e:
        print(f"Exact match error: {str(e)}")
    
    # If no exact matches, use semantic search
    try:
        all_data = CollegeData.objects.all()
        if all_data.exists():
            best_response = get_semantic_response(user_message, all_data)
            if best_response:
                if use_gemini:
                    return get_enhanced_response(user_message, context=best_response)
                return best_response
    except Exception as e:
        print(f"Semantic search error: {str(e)}")
    
    # If everything else fails, use Gemini or default response
    if use_gemini:
        return get_enhanced_response(user_message)
    return default_response()

def handle_quick_reply(user_message):
    """Handle predefined quick reply options"""
    quick_replies = {
        'college facilities': """Our campus features comprehensive facilities including:
- Modern classrooms and lecture halls
- Well-equipped laboratories
- Large library with study areas
- Sports facilities including indoor and outdoor courts
- Student cafeteria and food court
- Wi-Fi enabled campus
- Medical center
- Student recreation areas
Feel free to ask about any specific facility!""",

        'campus events': """We organize various events throughout the academic year:
- Cultural festivals and celebrations
- Technical symposiums and workshops
- Sports tournaments and competitions
- Club activities and performances
- Guest lectures and seminars
- Career fairs and placement drives
Ask me about any specific event you're interested in!""",

        'contact information': """Here's how you can reach us:
- Admissions Office: Contact for admission inquiries and procedures
- Academic Office: For course-related queries
- Student Affairs: For general student support
- Placement Cell: For career guidance and opportunities
- Department Offices: For specific course queries

Please ask for specific contact details you need!""",

        'admission process': """Our admission process includes:
1. Online application submission
2. Document verification
3. Entrance exam or merit-based selection
4. Counseling and seat allocation
5. Fee payment and enrollment

Would you like details about any specific step?""",

        'course information': """We offer various courses including:
- Undergraduate Programs (B.Tech, etc.)
- Postgraduate Programs (M.Tech, etc.)
- Diploma Courses
- Certificate Programs

Which course would you like to know more about?""",

        'class timetables': """Class schedules are organized as follows:
- Regular classes: Monday to Friday
- Practical sessions in laboratories
- Tutorial sessions for doubt clearing
- Extra-curricular activities
- Special workshops and seminars

Would you like specific timing details?""",

        'exam schedule': """Our examination system includes:
- Continuous Internal Assessments
- Mid-semester Examinations
- End-semester Examinations
- Practical Examinations
- Project Evaluations

Need information about any specific exam?""",

        'faculty information': """Our faculty members are:
- Highly qualified in their respective fields
- Experienced in teaching and research
- Actively involved in student mentoring
- Engaged in research and development
- Available for academic guidance

Would you like to know about specific departments?""",

        'student clubs': """We have various active student clubs:
- Technical Clubs
- Cultural Clubs
- Sports Clubs
- Literary Clubs
- Social Service Clubs
- Photography Club
- Coding Club

Which club interests you?""",

        'library hours': """Library facilities and timings:
- Open Monday to Saturday
- Extended hours during exams
- Digital library access
- Reading rooms
- Reference sections
- Journal sections

Need specific timing details?"""
    }

    # Check for exact matches first
    user_message = user_message.lower().strip()
    if user_message in quick_replies:
        return quick_replies[user_message]
    
    # Check for partial matches
    for key in quick_replies:
        if key in user_message:
            return quick_replies[key]
    
    return None

def get_best_category_response(matches, user_message):
    """Get the best response from a category based on relevance"""
    best_score = 0
    best_response = None
    
    for match in matches:
        # Calculate relevance score based on keyword matches
        score = sum(1 for keyword in match.keywords.split(',') if keyword.strip() in user_message)
        if score > best_score:
            best_score = score
            best_response = match.answer
    
    return best_response or random.choice(list(matches)).answer

def get_semantic_response(user_message, all_data):
    """Get the best response using semantic similarity"""
    try:
        corpus = [item.question for item in all_data]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
        user_vector = vectorizer.transform([user_message])
        
        similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
        best_match_index = similarities.argmax()
        
        if similarities[best_match_index] > 0.2:
            return all_data[best_match_index].answer
    except Exception as e:
        print(f"Semantic response error: {str(e)}")
    
    return None

def rule_based_response(user_message):
    # Extract keywords from user message
    keywords = extract_keywords(user_message)
    
    # Map of keywords to categories
    category_keywords = {
        'admission': ['admission', 'apply', 'enrollment', 'register', 'joining', 'entrance', 'test', 'application', 'requirements', 'deadline'],
        'exam': ['exam', 'test', 'schedule', 'result', 'grade', 'score', 'marks', 'semester', 'assessment', 'evaluation', 'timetable', 'date'],
        'academic': ['class', 'lecture', 'timetable', 'schedule', 'course', 'subject', 'timing', 'period', 'semester', 'academic', 'study'],
        'facilities': ['facility', 'lab', 'laboratory', 'library', 'canteen', 'cafeteria', 'wifi', 'internet', 'computer', 'sports', 'gym'],
        'events': ['event', 'fest', 'festival', 'celebration', 'cultural', 'technical', 'workshop', 'seminar', 'conference', 'competition'],
        'club': ['club', 'society', 'association', 'committee', 'group', 'team', 'organization', 'activity', 'extracurricular'],
        'hostel': ['hostel', 'accommodation', 'stay', 'room', 'dormitory', 'residence', 'housing', 'facility', 'mess'],
        'faculty': ['faculty', 'professor', 'teacher', 'instructor', 'staff', 'lecturer', 'department', 'expert', 'specialist'],
        'course': ['course', 'program', 'curriculum', 'syllabus', 'subject', 'study', 'branch', 'specialization', 'major'],
        'fee': ['fee', 'payment', 'tuition', 'cost', 'expense', 'scholarship', 'financial', 'aid', 'funding', 'loan'],
        'placement': ['placement', 'job', 'career', 'recruitment', 'internship', 'employment', 'opportunity', 'company', 'interview'],
        'transport': ['transport', 'bus', 'vehicle', 'timing', 'route', 'pickup', 'drop', 'schedule', 'travel'],
        'contact': ['contact', 'phone', 'email', 'address', 'location', 'reach', 'enquiry', 'information', 'help', 'support']
    }
    
    # Try to determine the category based on keywords
    user_category = None
    max_matches = 0
    
    for category, cat_keywords in category_keywords.items():
        matches = sum(1 for keyword in keywords if keyword in cat_keywords)
        if matches > max_matches:
            max_matches = matches
            user_category = category
    
    # If category found, get a random response from that category
    if user_category and max_matches > 0:
        try:
            category_obj = Category.objects.filter(name__icontains=user_category).first()
            if category_obj:
                data_points = CollegeData.objects.filter(category=category_obj)
                if data_points.exists():
                    return random.choice(list(data_points)).answer
        except:
            pass
    
    return None

def extract_keywords(text):
    # Simple keyword extraction
    text = text.lower()
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Split into words
    words = text.split()
    # Remove stop words (simplified list)
    stop_words = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 
                  'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 
                  'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 
                  'itself', 'they', 'them', 'their', 'theirs', 'themselves', 
                  'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 
                  'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 
                  'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 
                  'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 
                  'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
                  'into', 'through', 'during', 'before', 'after', 'above', 'below', 
                  'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 
                  'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 
                  'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 
                  'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 
                  'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
                  'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 
                  'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 
                  'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 
                  'wouldn', 'tell', 'know', 'want', 'like', 'need', 'help', 'hello', 'hi']
    
    keywords = [word for word in words if word not in stop_words]
    return keywords

def default_response():
    default_responses = [
        "I'd be happy to help you with information about our college. Could you please ask a more specific question about admissions, courses, facilities, or any other aspect?",
        "I can provide information about various aspects of our college. What specific details would you like to know?",
        "Please feel free to ask about specific topics like admissions, courses, facilities, faculty, or campus life. How can I assist you?",
        "I'm here to help! You can ask about our programs, campus facilities, admission process, or any other college-related information.",
        "To better assist you, could you please specify what information you're looking for? For example: admission process, course details, facilities, etc."
    ]
    return random.choice(default_responses)


# Gemini API configure karo
