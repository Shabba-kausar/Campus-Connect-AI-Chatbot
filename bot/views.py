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
            
            # Generate response using NLP
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
    
    # Try to find an exact match first
    try:
        exact_matches = CollegeData.objects.filter(
            keywords__icontains=user_message
        )
        if exact_matches.exists():
            return random.choice(list(exact_matches)).answer
    except:
        pass
    
    # If no exact matches, use NLP to find best match
    try:
        all_data = CollegeData.objects.all()
        corpus = [item.question for item in all_data] + [item.keywords for item in all_data]
        
        if not corpus:
            return default_response()
        
        # Use TF-IDF vectorization and cosine similarity
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
            user_vector = vectorizer.transform([user_message])
            
            # Calculate cosine similarity
            cosine_similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
            
            # Get best match index
            best_match_index = cosine_similarities.argmax()
            similarity_score = cosine_similarities[best_match_index]
            
            # If similarity score is good enough, return the corresponding answer
            if similarity_score > 0.2:  # Threshold can be adjusted
                index = best_match_index % len(all_data)  # Account for duplicate corpus
                return all_data[index].answer
        except:
            pass
    except:
        pass
    
    # Fallback to rule-based responses if NLP fails
    return rule_based_response(user_message) or default_response()

def rule_based_response(user_message):
    # Extract keywords from user message
    keywords = extract_keywords(user_message)
    
    # Map of keywords to categories
    category_keywords = {
        'admission': ['admission', 'apply', 'enrollment', 'register', 'joining', 'entrance', 'test'],
        'exam': ['exam', 'test', 'schedule', 'result', 'grade', 'score', 'marks', 'semester'],
        'fest': ['fest', 'festival', 'event', 'celebration', 'cultural', 'technical'],
        'club': ['club', 'society', 'association', 'committee', 'group', 'team'],
        'canteen': ['canteen', 'food', 'meal', 'eat', 'lunch', 'dinner', 'breakfast', 'menu'],
        'hostel': ['hostel', 'accommodation', 'stay', 'room', 'dormitory', 'residence'],
        'faculty': ['faculty', 'professor', 'teacher', 'instructor', 'staff', 'lecturer'],
        'course': ['course', 'program', 'curriculum', 'syllabus', 'subject', 'study'],
        'fee': ['fee', 'payment', 'tuition', 'cost', 'expense', 'scholarship', 'financial'],
        'placement': ['placement', 'job', 'career', 'recruitment', 'internship', 'employment']
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
        "I'm here to help with any questions related to Jorhat Engineering College! Feel free to ask about clubs, events, or facilities.",
        "I'm sorry, I didn't quite understand that. Could you please rephrase your question about JEC?",
        "I'd be happy to assist you with information about Jorhat Engineering College. Could you please provide more details?",
        "Feel free to ask me about admissions, exams, clubs, or any other aspect of JEC!",
        "I'm still learning, but I'll do my best to help you with your inquiries about Jorhat Engineering College."
    ]
    return random.choice(default_responses)