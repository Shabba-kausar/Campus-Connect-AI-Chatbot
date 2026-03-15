from .openai_helper import get_enhanced_response, is_query_suitable_for_llm, get_bot_reply
from django.conf import settings
from django.shortcuts import render

def index(request):
    """Render the main chatbot UI."""
    return render(request, 'index.html')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
from .models import Conversation, Message, CollegeData, Category
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import requests
from urllib.parse import urljoin, urlparse
# Semantic search imports
from sentence_transformers import SentenceTransformer
# Local utilities for live fetch + summarization
from utils.web_fetcher import fetch_from_web
from utils.summarizer import summarize_with_gpt
import json as _json
BACKUP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'backup_data.json')

EMBEDDINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'manuu_embeddings.npy')
CHUNKS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'manuu_chunks_index.txt')
MODEL_NAME = 'all-MiniLM-L6-v2'

# Allowed MANUU Hyderabad base URLs (only fetch from these)
# Authorized Data Source URLs from official requirements
ALLOWED_BASES = [
    'https://manuu.edu.in/',
    'https://manuu.edu.in/About-MANUU',
    'https://manuu.edu.in/Academics',
    'https://manuu.edu.in/Schools',
    'https://manuu.edu.in/Programs',
    'https://manuu.edu.in/admissions',
    'https://manuu.edu.in/Examination',
    'https://manuu.edu.in/Hostels',
    'https://manuu.edu.in/Campus-Life',
    'https://manuu.edu.in/Faculty',
    'https://manuu.edu.in/Events',
    'https://manuu.edu.in/Contact-Us',
    # CSIT Department URLs - Approved Live Data Sources
    'https://manuu.edu.in/University/SCSIT/CSIT/Profile',
    'https://manuu.edu.in/University/SCSIT/CSIT/People',
    'https://manuu.edu.in/University/SCSIT/CSIT/People/741',
    'https://manuu.edu.in/University/SCSIT/People/581',
    'https://manuu.edu.in/University/SCSIT/CSIT/Programs-Syllabus',
    'https://manuu.edu.in/University/CSIT/BOS/minutes',
    'https://manuu.edu.in/University/SCSIT/CSIT/Committees/Departmental-Research-Committee',
    'https://manuu.edu.in/University/SCSIT/CSIT/MOMs/Departmental-Research-Committee',
    'https://manuu.edu.in/University/SCSIT/CSIT/major-project',
    'https://manuu.edu.in/University/SCSIT/CSIT/minor-project',
    'https://manuu.edu.in/University/SCSIT/CSIT/Research-Scholars',
    'https://manuu.edu.in/University/SCSIT/CSIT/Research-Publications',
    'https://manuu.edu.in/University/School/SCSIT/Profile',
    'https://manuu.edu.in/University/School/SCSIT/ContactUs',
    'https://manuu.edu.in/University/SCSIT/CSIT/Resources/Class-Time-Table',
    'https://manuu.edu.in/University/SCSIT/CSIT/notifications',
    'https://manuu.edu.in/University/SCSIT/CSIT/TP-cell',
    'https://manuu.edu.in/University/SCSIT/CSIT/Resources/Students-Details',
    'https://manuu.edu.in/University/SCSIT/CSIT/Facilities',
]

def is_allowed_manuu_url(u: str) -> bool:
    if not u:
        return False
    lu = u.lower()
    for b in ALLOWED_BASES:
        if lu.startswith(b):
            return True
    # some discovered URLs use /University/ path; allow any under manuu.edu.in domain
    if lu.startswith('https://manuu.edu.in/'):
        return True
    return False

# --- MANUU Hyderabad-specific helpers
def format_structured_reply(title: str, bullets: list) -> str:
    """Return a small structured reply: single heading + 2-5 bullets."""
    # Keep it short: limit to first 5 bullets
    bullets = bullets[:5]
    body = "\n".join(f"- {b.strip()}" for b in bullets if b and b.strip())
    return f"{title}\n\n{body}"


def manuu_fallback_url(user_message: str) -> str:
    """Return the most relevant MANUU Hyderabad URL for a user_message.

    This is a simple keyword-based mapping that prioritizes Hyderabad campus
    pages under https://manuu.edu.in/. Uses authorized URLs only.
    If no specific match, return the main site URL.
    """
    mapping = {
        'admission': 'https://manuu.edu.in/admissions',
        'about': 'https://manuu.edu.in/About-MANUU',
        'academics': 'https://manuu.edu.in/Academics',
        'schools': 'https://manuu.edu.in/Schools',
        'programs': 'https://manuu.edu.in/Programs',
        'courses': 'https://manuu.edu.in/Programs',
        'examination': 'https://manuu.edu.in/Examination',
        'exam': 'https://manuu.edu.in/Examination',
        'hostel': 'https://manuu.edu.in/Hostels',
        'campus': 'https://manuu.edu.in/Campus-Life',
        'faculty': 'https://manuu.edu.in/Faculty',
        'events': 'https://manuu.edu.in/Events',
        'contact': 'https://manuu.edu.in/Contact-Us',
        'csit': 'https://manuu.edu.in/University/SCSIT/CSIT/People',
        'computer': 'https://manuu.edu.in/University/SCSIT/CSIT/People',
        'it': 'https://manuu.edu.in/University/SCSIT/CSIT/People',
        'library': 'https://manuu.edu.in/',
        'canteen': 'https://manuu.edu.in/Campus-Life',
        'facilities': 'https://manuu.edu.in/Campus-Life',
        'map': 'https://manuu.edu.in/About-MANUU',
        'placement': 'https://manuu.edu.in/',
    }
    um = user_message.lower()
    # Try mapped URL first; if it does not return a 2xx, try to discover a working URL
    def is_url_ok(u: str) -> bool:
        try:
            # Prefer HEAD to avoid full content, allow redirects
            resp = requests.head(u, allow_redirects=True, timeout=8)
            if resp.status_code >= 200 and resp.status_code < 300:
                return True
            # Some servers disallow HEAD; try GET
            resp = requests.get(u, allow_redirects=True, timeout=8)
            return 200 <= resp.status_code < 300
        except Exception:
            return False

    for k, v in mapping.items():
        if k in um:
            # If mapped URL is valid, return it
            if is_url_ok(v) and is_allowed_manuu_url(v):
                return v
            # Otherwise, try to discover a link on the MANUU homepage
            try:
                homepage = 'https://manuu.edu.in/'
                h = requests.get(homepage, timeout=8)
                if h.status_code == 200:
                    # find anchors that include the keyword
                    import re
                    anchors = re.findall(r'href="([^"]+)"', h.text)
                    for a in anchors:
                        # normalize relative links
                        href = a
                        if href.startswith('/'):
                            candidate = 'https://manuu.edu.in' + href
                        elif href.startswith('http'):
                            candidate = href
                        else:
                            continue
                        if k in candidate.lower() or k in href.lower():
                            if is_url_ok(candidate) and is_allowed_manuu_url(candidate):
                                return candidate
            except Exception:
                pass
            # Final fallback for this keyword: return the mapped value even if it may 404
            return v
    # No keyword matched: return the main site
    return 'https://manuu.edu.in/'


def get_cached_site_url(user_message: str) -> str:
    """Return a validated site URL for the user_message using data/site_urls.json when available.

    Falls back to manuu_fallback_url if the cache file is missing or no key matches.
    """
    try:
        data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'site_urls.json')
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as rf:
                mapping = _json.load(rf)
            um = user_message.lower()
            for k, v in mapping.items():
                if k in um:
                    # only return mapped value if it is within allowed MANUU domain
                    if is_allowed_manuu_url(v):
                        return v
                    return 'https://manuu.edu.in/'
    except Exception:
        pass
    return manuu_fallback_url(user_message)


def discover_and_persist_site_urls():
    """Crawl the MANUU homepage for anchors and build a mapping for known topics.

    Writes a small JSON file at data/site_urls.json containing discovered
    working URLs for topics we care about. This reduces runtime discovery
    latency on subsequent requests.
    """
    try:
        homepage = 'https://manuu.edu.in/'
        r = requests.get(homepage, timeout=10)
        if r.status_code != 200:
            return None
        text = r.text
        import re
        anchors = re.findall(r'href\s*=\s*"([^"]+)"', text)
        anchors = list(dict.fromkeys(anchors))
        candidates = []
        for a in anchors:
            if a.startswith('/'):
                candidates.append(urljoin(homepage, a))
            elif a.startswith('http'):
                candidates.append(a)

        topics = {
            'admission': 'admission',
            'courses': 'course',
            'hostel': 'hostel',
            'library': 'library',
            'placement': 'placement',
            'examination': 'exam',
            'contact': 'contact',
            'facilities': 'facility',
            'map': 'about'
        }

        found = {}
        for k in topics.keys():
            # try direct mapping patterns first
            for c in candidates:
                lk = c.lower()
                if k in lk or topics[k] in lk:
                    try:
                        rr = requests.head(c, allow_redirects=True, timeout=6)
                        if 200 <= rr.status_code < 400:
                            found[k] = c
                            break
                    except Exception:
                        try:
                            rr = requests.get(c, allow_redirects=True, timeout=6)
                            if 200 <= rr.status_code < 400:
                                found[k] = c
                                break
                        except Exception:
                            pass
            # no direct candidate found -> fallback to homepage
            if k not in found:
                found[k] = homepage

        # persist to data/site_urls.json
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            target = os.path.join(data_dir, 'site_urls.json')
            with open(target, 'w', encoding='utf-8') as wf:
                _json.dump(found, wf, indent=2)
            return found
        except Exception:
            return found
    except Exception:
        return None


def handle_visual_query(user_message: str):
    """Handle visual queries (campus map, building image, auditorium).

    This will ensure a simple illustrative SVG exists under static and
    return a structured reply containing a relative image path.
    """
    STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'generated_images')
    os.makedirs(STATIC_DIR, exist_ok=True)
    svg_path = os.path.join(STATIC_DIR, 'manuu_hyderabad_map.svg')
    rel_url = '/static/generated_images/manuu_hyderabad_map.svg'

    # Create a very small illustrative SVG if it doesn't exist
    if not os.path.exists(svg_path):
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500">
  <rect width="100%" height="100%" fill="#f7f7f7" />
  <text x="50%" y="8%" font-size="22" text-anchor="middle" fill="#222">MANUU Hyderabad - Illustrative Campus Map</text>
  <rect x="40" y="60" width="220" height="120" rx="10" fill="#cfe8ff" stroke="#0066cc" />
  <text x="150" y="130" font-size="14" text-anchor="middle" fill="#003366">Library</text>
  <rect x="300" y="60" width="220" height="120" rx="10" fill="#e6ffd9" stroke="#278a0f" />
  <text x="410" y="130" font-size="14" text-anchor="middle" fill="#155607">Auditorium</text>
  <rect x="40" y="200" width="220" height="120" rx="10" fill="#fff1d6" stroke="#cc8800" />
  <text x="150" y="270" font-size="14" text-anchor="middle" fill="#6b3f00">Hostels</text>
  <rect x="300" y="200" width="220" height="120" rx="10" fill="#ffe6f0" stroke="#cc0066" />
  <text x="410" y="270" font-size="14" text-anchor="middle" fill="#88003a">Canteen</text>
  <text x="50" y="480" font-size="12" fill="#444">Note: This is an illustrative map generated by the chatbot. For the official campus map and directions, visit https://manuu.edu.in/</text>
</svg>'''
        try:
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
        except Exception as _:
            pass

    # Prefer to fetch a live image from the official site for freshness
    try:
        # Check if this is a CSIT-related visual query
        um_lower_viz = user_message.lower()
        csit_viz_keywords = ['csit', 'computer science', 'cs department', 'it department', 'scsit']
        is_csit_visual = any(kw in um_lower_viz for kw in csit_viz_keywords)
        
        # Determine a candidate page for the visual query
        if is_csit_visual:
            # For CSIT visual queries, use CSIT-specific URLs
            if 'timetable' in um_lower_viz or 'schedule' in um_lower_viz or 'time table' in um_lower_viz:
                candidate_page = 'https://manuu.edu.in/University/SCSIT/CSIT/Resources/Class-Time-Table'
            elif 'lab' in um_lower_viz or 'laboratory' in um_lower_viz or 'facility' in um_lower_viz or 'facilities' in um_lower_viz:
                candidate_page = 'https://manuu.edu.in/University/SCSIT/CSIT/Facilities'
            elif 'project' in um_lower_viz:
                # Try major project first, then minor
                candidate_page = 'https://manuu.edu.in/University/SCSIT/CSIT/major-project'
            elif 'building' in um_lower_viz or 'campus' in um_lower_viz:
                candidate_page = 'https://manuu.edu.in/University/SCSIT/CSIT/Profile'
            else:
                candidate_page = 'https://manuu.edu.in/University/SCSIT/CSIT/Profile'
        else:
            candidate_page = manuu_fallback_url(user_message)
        imgs = []
        try:
            pr = requests.get(candidate_page, timeout=8)
            if pr.status_code == 200:
                import re
                srcs = re.findall(r'<img[^>]+src="([^"]+)"', pr.text)
                # normalize and filter
                for s in srcs:
                    if s.startswith('//'):
                        s = 'https:' + s
                    elif s.startswith('/'):
                        s = urljoin(candidate_page, s)
                    elif not s.startswith('http'):
                        s = urljoin(candidate_page, s)
                    # prefer images with keywords based on query type
                    alt_score = 0
                    low = s.lower()
                    um_low = user_message.lower()
                    
                    # Check for specific matches based on query type
                    if 'csit' in um_low or 'computer' in um_low:
                        # CSIT-specific image priorities
                        if 'timetable' in um_low or 'schedule' in um_low:
                            if any(x in low for x in ['timetable', 'schedule', 'time', 'table']):
                                imgs.insert(0, s)
                                continue
                        elif 'lab' in um_low or 'laboratory' in um_low or 'facility' in um_low:
                            if any(x in low for x in ['lab', 'laboratory', 'facility', 'equipment', 'computer']):
                                imgs.insert(0, s)
                                continue
                        elif 'project' in um_low:
                            if any(x in low for x in ['project', 'research', 'student']):
                                imgs.insert(0, s)
                                continue
                        elif any(x in low for x in ['csit', 'computer', 'it', 'scsit', 'building']):
                            imgs.insert(0, s)
                            continue
                    
                    # General image matching
                    if any(x in low for x in ['campus', 'library', 'auditorium', 'hostel', 'canteen', 'building', 'csit', 'computer', 'lab', 'timetable']):
                        imgs.insert(0, s)
                    else:
                        imgs.append(s)
        except Exception:
            imgs = []

        # Download the first useful image if any
        image_rel = None
        if imgs:
            for idx, src in enumerate(imgs):
                try:
                    rimg = requests.get(src, timeout=8)
                    if rimg.status_code == 200 and int(rimg.headers.get('content-length', '0')) > 5000:
                        # save to static/generated_images
                        img_ext = os.path.splitext(urlparse(src).path)[1] or '.jpg'
                        fname = f"manuu_visual_{idx}{img_ext}"
                        out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'generated_images')
                        os.makedirs(out_dir, exist_ok=True)
                        out_path = os.path.join(out_dir, fname)
                        with open(out_path, 'wb') as wf:
                            wf.write(rimg.content)
                        image_rel = '/static/generated_images/' + fname
                        break
                except Exception:
                    continue

        # If we didn't download a live image, fall back to the illustrative SVG
        if not image_rel:
            image_rel = rel_url

        # Build structured reply with the image
        # Per requirements: If a user asks for visuals, auto-generate or attach a relevant image
        title = 'Campus Visual'
        bullets = [
            'Auto-generated or official image for the requested location.',
            f'Source: {candidate_page}',
            'For official high-resolution images, visit the MANUU website.'
        ]
        reply = format_structured_reply(title, bullets)
        reply = reply + f"\n\n[IMAGE] {image_rel}"
        # Include source URL reference as per requirements
        if candidate_page:
            reply = reply + f"\n\n➡️ For more information, visit: {candidate_page}"
        return reply
    except Exception:
        # Hard fallback to illustrative SVG reply
        title = 'Campus Map / Visual'
        bullets = [
            'Auto-generated illustrative campus map for MANUU Hyderabad.',
            'Sections marked: Library, Auditorium, Hostels, Canteen.',
            'For the official map and directions, please visit the MANUU website.'
        ]
        reply = format_structured_reply(title, bullets)
        reply = reply + f"\n\n[IMAGE] {rel_url}"
        reply = reply + f"\n\n➡️ For more information, visit: https://manuu.edu.in/"
        return reply


def semantic_search_response(user_message):
    """Return the most relevant chunk from MANUU data using semantic search.

    This function caches the model, embeddings and chunks on the function object
    to avoid reloading on every request. It returns a plain string (the best
    matching chunk) or a friendly 'not found' message.
    """
    try:
        # Lazy-load model, embeddings and chunks
        if not hasattr(semantic_search_response, 'model'):
            semantic_search_response.model = SentenceTransformer(MODEL_NAME)

        if not hasattr(semantic_search_response, 'embeddings'):
            if os.path.exists(EMBEDDINGS_PATH):
                with open(EMBEDDINGS_PATH, 'rb') as ef:
                    semantic_search_response.embeddings = np.load(ef)
            else:
                semantic_search_response.embeddings = None

        if not hasattr(semantic_search_response, 'all_chunks'):
            if os.path.exists(CHUNKS_PATH):
                with open(CHUNKS_PATH, 'r', encoding='utf-8') as cf:
                    semantic_search_response.all_chunks = [ln.strip() for ln in cf if ln.strip()]
            else:
                semantic_search_response.all_chunks = None

        # If we don't have precomputed embeddings/chunks, bail out early
        if semantic_search_response.embeddings is None or semantic_search_response.all_chunks is None:
            return "Please visit https://manuu.edu.in/ for the most updated information."

        # Encode the user message and compute cosine similarities
        user_emb = semantic_search_response.model.encode([user_message])
        sims = cosine_similarity(user_emb, semantic_search_response.embeddings)[0]
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])

        # Debug log
        print(f"[semantic_search_response] best_score={best_score}, best_idx={best_idx}")

        # Threshold to decide if a chunk is relevant
        if best_score > 0.30 and best_idx < len(semantic_search_response.all_chunks):
            return semantic_search_response.all_chunks[best_idx]
        return "Please visit https://manuu.edu.in/ for the most updated information."
    except Exception as e:
        print(f"[semantic_search_response] Exception: {e}")
        return "Please visit https://manuu.edu.in/ for the most updated information."


def reply_matches_context(reply: str, context: str, threshold: float = 0.05) -> bool:
    """Return True if the reply shares enough token overlap with context.

    Simple heuristic: tokenize words, remove short stop-words, and compute the
    fraction of reply tokens that appear in the context. If below threshold,
    treat as likely hallucination.
    """
    try:
        if not reply or not context:
            return False
        # Basic tokenization
        def normalize(s):
            return re.sub(r"[^a-z0-9\s]", " ", s.lower())

        reply_tokens = [t for t in normalize(reply).split() if len(t) > 2]
        context_tokens = set([t for t in normalize(context).split() if len(t) > 2])
        if not reply_tokens:
            return False
        match_count = sum(1 for t in reply_tokens if t in context_tokens)
        ratio = match_count / len(reply_tokens)
        print(f"[reply_matches_context] match_count={match_count}, reply_len={len(reply_tokens)}, ratio={ratio:.2f}")
        return ratio >= threshold
    except Exception as e:
        print(f"[reply_matches_context] Exception: {e}")
        return False


@csrf_exempt
def process_message(request):
    if request.method == 'POST':
        try:
            raw_body = request.body.decode('utf-8') if isinstance(request.body, (bytes, bytearray)) else str(request.body)
            print(f"[process_message] Raw body: {raw_body}")
            data = json.loads(raw_body)
            user_message = data.get('message', '').strip()
            user_identifier = data.get('user_id', '')

            if not user_message:
                return JsonResponse({'error': 'Empty message received'}, status=400)

            # Safely get or create a conversation. Some previous runs created
            # multiple Conversation rows for the same identifier; use filter()
            # and create a new one if none exists.
            conversation = None
            if user_identifier:
                conversation = Conversation.objects.filter(user_identifier=user_identifier).first()
            if not conversation:
                conversation = Conversation.objects.create(user_identifier=user_identifier)

            # Save user message using the Message model fields: 'sender' and 'content'
            Message.objects.create(
                conversation=conversation,
                sender='user',
                content=str(user_message)
            )

            # Generate and save bot response. generate_response now returns a
            # tuple (text, source_url) when the response was produced by
            # live-fetching an official page; source_url is None otherwise.
            result = generate_response(user_message)
            if isinstance(result, tuple) and len(result) == 2:
                bot_response, source_url = result
            else:
                bot_response = result
                source_url = None
            # If the response was produced by live-fetching an official page,
            # include the source URL in the visible message so users get both
            # the fetched summary and the official link.
            try:
                if source_url:
                    # Only append trusted manuu links to avoid unrelated URLs
                    bot_response = f"{bot_response}\n\nFor more information: {source_url}"
            except Exception:
                pass
            # Ensure we always store a string using correct fields
            Message.objects.create(
                conversation=conversation,
                sender='bot',
                content=str(bot_response)
            )

            print(f"[process_message] Generated bot_response: {repr(bot_response)}")

            # Optional debug info included only in DEBUG mode or when DEV_DEBUG=1
            debug_enabled = os.getenv('DEV_DEBUG', '0') == '1' or getattr(settings, 'DEBUG', False)
            response_payload = {
                'message': bot_response,
                'user_id': conversation.user_identifier or str(conversation.id)
            }
            if debug_enabled:
                try:
                    mock_mode = os.getenv('MOCK_OPENAI', '0').lower() in ('1', 'true', 'yes')
                    embeds_exist = os.path.exists(EMBEDDINGS_PATH)
                    chunks_exist = os.path.exists(CHUNKS_PATH)
                    sem_chunk = semantic_search_response(user_message)
                    response_payload['debug'] = {
                        'mock_mode': mock_mode,
                        'embeddings_present': embeds_exist,
                        'chunks_present': chunks_exist,
                        'semantic_chunk_preview': (sem_chunk[:300] + '...') if isinstance(sem_chunk, str) and len(sem_chunk) > 300 else sem_chunk,
                        'source_url': source_url
                    }
                except Exception as _:
                    response_payload['debug'] = {'error': 'failed to build debug info'}

            return JsonResponse(response_payload)

        except json.JSONDecodeError:
            err_msg = 'Invalid JSON in request body'
            print(f"[process_message] JSONDecodeError: {err_msg}")
            return JsonResponse({'message': default_response(), 'error': err_msg}, status=400)
        except Exception as e:
            err = str(e)
            # Log server-side for debugging; frontend receives a friendly fallback message
            print(f"[process_message] Exception: {err}")
            return JsonResponse({'message': default_response(), 'error': err}, status=500)

    # Non-POST requests return a friendly fallback message so the frontend always
    # receives a `message` key and can render something useful.
    return JsonResponse({'message': default_response(), 'error': 'Invalid request method'}, status=400)

def handle_csit_query(user_message: str):
    """Handle CSIT-specific queries by fetching live data from approved CSIT URLs.
    
    Maps user queries to relevant CSIT URLs and fetches/summarizes the content.
    Returns a tuple (response_text, source_urls_list) or None if not CSIT-related.
    """
    um_lower = user_message.lower()
    
    # CSIT query detection - expanded triggers
    csit_keywords = ['csit', 'computer science', 'cs department', 'it department', 
                     'school of cs', 'scsit', 'cse', 'computer engineering']
    
    if not any(kw in um_lower for kw in csit_keywords):
        return None
    
    # Map query types to relevant CSIT URLs
    csit_url_mapping = {
        # Faculty and People queries
        'faculty': ['https://manuu.edu.in/University/SCSIT/CSIT/People'],
        'professor': ['https://manuu.edu.in/University/SCSIT/CSIT/People'],
        'teacher': ['https://manuu.edu.in/University/SCSIT/CSIT/People'],
        'staff': ['https://manuu.edu.in/University/SCSIT/CSIT/People'],
        'people': ['https://manuu.edu.in/University/SCSIT/CSIT/People'],
        
        # Profile and About
        'profile': ['https://manuu.edu.in/University/SCSIT/CSIT/Profile'],
        'about': ['https://manuu.edu.in/University/SCSIT/CSIT/Profile', 
                  'https://manuu.edu.in/University/School/SCSIT/Profile'],
        'department': ['https://manuu.edu.in/University/SCSIT/CSIT/Profile'],
        
        # Programs and Syllabus
        'program': ['https://manuu.edu.in/University/SCSIT/CSIT/Programs-Syllabus'],
        'syllabus': ['https://manuu.edu.in/University/SCSIT/CSIT/Programs-Syllabus'],
        'course': ['https://manuu.edu.in/University/SCSIT/CSIT/Programs-Syllabus'],
        'curriculum': ['https://manuu.edu.in/University/SCSIT/CSIT/Programs-Syllabus'],
        
        # Timetable
        'timetable': ['https://manuu.edu.in/University/SCSIT/CSIT/Resources/Class-Time-Table'],
        'schedule': ['https://manuu.edu.in/University/SCSIT/CSIT/Resources/Class-Time-Table'],
        'class time': ['https://manuu.edu.in/University/SCSIT/CSIT/Resources/Class-Time-Table'],
        'time table': ['https://manuu.edu.in/University/SCSIT/CSIT/Resources/Class-Time-Table'],
        
        # Research
        'research': ['https://manuu.edu.in/University/SCSIT/CSIT/Research-Publications',
                     'https://manuu.edu.in/University/SCSIT/CSIT/Research-Scholars'],
        'publication': ['https://manuu.edu.in/University/SCSIT/CSIT/Research-Publications'],
        'scholar': ['https://manuu.edu.in/University/SCSIT/CSIT/Research-Scholars'],
        
        # Projects
        'major project': ['https://manuu.edu.in/University/SCSIT/CSIT/major-project'],
        'minor project': ['https://manuu.edu.in/University/SCSIT/CSIT/minor-project'],
        'project': ['https://manuu.edu.in/University/SCSIT/CSIT/major-project',
                    'https://manuu.edu.in/University/SCSIT/CSIT/minor-project'],
        
        # Committees
        'committee': ['https://manuu.edu.in/University/SCSIT/CSIT/Committees/Departmental-Research-Committee'],
        'research committee': ['https://manuu.edu.in/University/SCSIT/CSIT/Committees/Departmental-Research-Committee'],
        
        # Notifications
        'notification': ['https://manuu.edu.in/University/SCSIT/CSIT/notifications'],
        'notice': ['https://manuu.edu.in/University/SCSIT/CSIT/notifications'],
        'announcement': ['https://manuu.edu.in/University/SCSIT/CSIT/notifications'],
        
        # Placement/Training
        'placement': ['https://manuu.edu.in/University/SCSIT/CSIT/TP-cell'],
        'training': ['https://manuu.edu.in/University/SCSIT/CSIT/TP-cell'],
        'tp cell': ['https://manuu.edu.in/University/SCSIT/CSIT/TP-cell'],
        
        # Contact
        'contact': ['https://manuu.edu.in/University/School/SCSIT/ContactUs'],
        'address': ['https://manuu.edu.in/University/School/SCSIT/ContactUs'],
        
        # Students
        'student': ['https://manuu.edu.in/University/SCSIT/CSIT/Resources/Students-Details'],
        
        # Facilities
        'facility': ['https://manuu.edu.in/University/SCSIT/CSIT/Facilities'],
        'facilities': ['https://manuu.edu.in/University/SCSIT/CSIT/Facilities'],
        'lab': ['https://manuu.edu.in/University/SCSIT/CSIT/Facilities'],
        'laboratory': ['https://manuu.edu.in/University/SCSIT/CSIT/Facilities'],
        'infrastructure': ['https://manuu.edu.in/University/SCSIT/CSIT/Facilities'],
        
        # Specific faculty profiles (Dean, HOD)
        'dean': ['https://manuu.edu.in/University/SCSIT/People/581'],
        'hod': ['https://manuu.edu.in/University/SCSIT/CSIT/People/741'],
        'head of department': ['https://manuu.edu.in/University/SCSIT/CSIT/People/741'],
        'prof. abdul wahid': ['https://manuu.edu.in/University/SCSIT/People/581'],
        'prof. pradeep kumar': ['https://manuu.edu.in/University/SCSIT/CSIT/People/741'],
    }
    
    # Determine which URLs to fetch based on query
    urls_to_fetch = []
    for keyword, urls in csit_url_mapping.items():
        if keyword in um_lower:
            urls_to_fetch.extend(urls)
            break
    
    # If no specific match, default to Profile and People pages
    if not urls_to_fetch:
        urls_to_fetch = [
            'https://manuu.edu.in/University/SCSIT/CSIT/Profile',
            'https://manuu.edu.in/University/SCSIT/CSIT/People'
        ]
    
    # Also include specific faculty URLs if query mentions dean or hod
    if 'dean' in um_lower or 'school of technology' in um_lower:
        dean_url = 'https://manuu.edu.in/University/SCSIT/People/581'
        if dean_url not in urls_to_fetch:
            urls_to_fetch.append(dean_url)
    
    if 'hod' in um_lower or 'head of department' in um_lower or 'pradeep kumar' in um_lower:
        hod_url = 'https://manuu.edu.in/University/SCSIT/CSIT/People/741'
        if hod_url not in urls_to_fetch:
            urls_to_fetch.append(hod_url)
    
    # Remove duplicates while preserving order
    seen = set()
    urls_to_fetch = [url for url in urls_to_fetch if url not in seen and not seen.add(url)]
    
    # Fetch and summarize content from relevant URLs
    all_content = []
    successful_urls = []
    
    for url in urls_to_fetch[:3]:  # Limit to 3 URLs to avoid too long responses
        try:
            live_text = fetch_from_web(url, max_chars=3000)
            if live_text and live_text.strip():
                all_content.append(live_text)
                successful_urls.append(url)
        except Exception as e:
            print(f"[handle_csit_query] Failed to fetch {url}: {e}")
            continue
    
    if not all_content or not successful_urls:
        # Fallback message as per requirements
        fallback_msg = "I couldn't find updated details on the official MANUU CSIT site. Please visit https://manuu.edu.in/University/SCSIT/CSIT for more information."
        return (fallback_msg, ['https://manuu.edu.in/University/SCSIT/CSIT'])
    
    # Combine all content and summarize
    # Mark content from each URL for better context
    combined_content_parts = []
    for idx, (content, url) in enumerate(zip(all_content, successful_urls), 1):
        combined_content_parts.append(f"[Content from {url}]\n{content}")
    combined_content = "\n\n---\n\n".join(combined_content_parts)
    
    try:
        # Use enhanced summarization that filters out irrelevant content
        summary = summarize_with_gpt(combined_content, user_message)
        if summary and not summary.strip().startswith('[summarizer error]'):
            # Format response with Official Sources section
            response_text = summary
            
            # Ensure Official Sources section is present (even if LLM didn't add it)
            if successful_urls:
                # Check if Official Sources section already exists
                if "📎 Official Sources" not in response_text and "Official Sources" not in response_text:
                    response_text += "\n\n📎 Official Sources:"
                    for url in successful_urls:
                        response_text += f"\n- {url}"
                # If it exists but URLs are missing, ensure all URLs are listed
                elif "📎 Official Sources" in response_text or "Official Sources" in response_text:
                    # Verify all URLs are mentioned
                    for url in successful_urls:
                        if url not in response_text:
                            # Append missing URLs
                            if response_text.endswith('\n'):
                                response_text += f"- {url}\n"
                            else:
                                response_text += f"\n- {url}"
            
            return (response_text, successful_urls)
    except Exception as e:
        print(f"[handle_csit_query] Summarization error: {e}")
    
    # If summarization fails, return a clean extract with sources
    # Try to extract meaningful sentences (at least 20 chars, not just navigation)
    sentences = []
    for content in all_content:
        # Split into sentences and filter
        content_sentences = re.split(r'[.!?]\s+', content)
        for sent in content_sentences:
            sent = sent.strip()
            # Filter out very short sentences, navigation items, and repetitive patterns
            if (len(sent) > 30 and 
                not re.match(r'^(Home|About|Contact|Search|Menu|Navigation)', sent, re.I) and
                not re.match(r'^[A-Z][a-z]+\s*:\s*$', sent)):  # Filter "Label: " patterns
                sentences.append(sent)
                if len(' '.join(sentences)) > 800:  # Limit total length
                    break
        if len(' '.join(sentences)) > 800:
            break
    
    response_text = ' '.join(sentences[:15])  # Limit to 15 most relevant sentences
    if len(response_text) > 1000:
        response_text = response_text[:1000] + "..."
    
    if successful_urls:
        response_text += "\n\n📎 Official Sources:"
        for url in successful_urls:
            response_text += f"\n- {url}"
    
    return (response_text, successful_urls)


def generate_response(user_message):
    user_message = user_message.strip()
    um_lower = user_message.lower()
    
    # Visual queries: check before CSIT handler if it's explicitly a visual request
    # This allows "show CSIT timetable image" to be handled as visual
    visual_keywords = ['image', 'picture', 'photo', 'show me', 'display', 'visual', 'map', 'show', 'see']
    is_visual_request = any(kw in um_lower for kw in visual_keywords)
    visual_triggers = ['campus map', 'map', 'library building', 'auditorium', 'campus map image', 
                       'map image', 'library image', 'auditorium image', 'csit building', 'building image',
                       'timetable image', 'schedule image', 'lab image', 'laboratory image', 'project image',
                       'timetable', 'schedule', 'lab', 'laboratory', 'facility', 'facilities']
    
    # For CSIT visual queries (labs, timetable, projects), handle as visual
    csit_visual_keywords = ['csit', 'computer science', 'cs department', 'it department']
    is_csit_visual = any(kw in um_lower for kw in csit_visual_keywords) and is_visual_request
    
    if (is_visual_request and any(t in um_lower for t in visual_triggers)) or is_csit_visual:
        return handle_visual_query(user_message)
    
    # CSIT/Computer Science/IT department queries - check after visual (for text-based CSIT queries)
    # This allows CSIT timetable text queries to go to CSIT handler
    csit_result = handle_csit_query(user_message)
    if csit_result:
        response_text, source_urls = csit_result
        # Return tuple for process_message to handle source URLs
        if isinstance(source_urls, list) and len(source_urls) > 0:
            # Return first URL as primary source for backwards compatibility
            return (response_text, source_urls[0])
        return response_text
    
    # Enforce exam-related instruction: direct users to the Examination Cell
    # Exact phrasing as per requirements (only for non-CSIT exam queries)
    exam_triggers = ['exam', 'exam date', 'exam dates', 'midterm', 'internal marks', 'marks', 'backlog', 'result', 'internal']
    # Exclude timetable from exam triggers if it's a general query (CSIT timetable already handled above)
    if any(t in um_lower for t in exam_triggers) and 'timetable' not in um_lower:
        # Exact phrasing requested by user policy
        return "Please contact the MANUU Examination Cell for accurate updates."
    
    # Visual queries (fallback for non-CSIT visual queries)
    if any(t in um_lower for t in visual_triggers):
        return handle_visual_query(user_message)
    # 1. Quick replies: return immediately (fast). Live fetch is handled inside
    #    handle_quick_reply with caching and preferred URLs.
    quick_reply_response = handle_quick_reply(user_message.lower())
    if quick_reply_response:
        return quick_reply_response
    # Also try a rule-based fallback early for short topical queries
    rb_early = rule_based_response(user_message)
    if rb_early:
        return rb_early
    # 1b. Try live website fetch -> summarizer -> return structured reply
    # Prefer dynamic site URL mapping if available (generated by site_crawler)
    SITE_URLS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'site_urls.json')
    URLS = None
    try:
        if os.path.exists(SITE_URLS_PATH):
            with open(SITE_URLS_PATH, 'r', encoding='utf-8') as sf:
                URLS = _json.load(sf)
    except Exception:
        URLS = None

    if not URLS:
        # default fallback mapping using authorized URLs
        URLS = {
            "admission": "https://manuu.edu.in/admissions",
            "about": "https://manuu.edu.in/About-MANUU",
            "academics": "https://manuu.edu.in/Academics",
            "schools": "https://manuu.edu.in/Schools",
            "programs": "https://manuu.edu.in/Programs",
            "examination": "https://manuu.edu.in/Examination",
            "hostel": "https://manuu.edu.in/Hostels",
            "campus": "https://manuu.edu.in/Campus-Life",
            "faculty": "https://manuu.edu.in/Faculty",
            "events": "https://manuu.edu.in/Events",
            "contact": "https://manuu.edu.in/Contact-Us",
            # CSIT URLs - Note: CSIT queries are now handled by handle_csit_query()
            "csit": "https://manuu.edu.in/University/SCSIT/CSIT/Profile",
            "computer": "https://manuu.edu.in/University/SCSIT/CSIT/Profile",
            "it": "https://manuu.edu.in/University/SCSIT/CSIT/Profile",
        }
    # identify a key (skip if CSIT query, as it's already handled by handle_csit_query)
    um_lower_check = user_message.lower()
    csit_keywords_check = ['csit', 'computer science', 'cs department', 'it department', 
                           'school of cs', 'scsit', 'cse', 'computer engineering']
    is_csit_query = any(kw in um_lower_check for kw in csit_keywords_check)
    
    key = next((k for k in URLS if k in um_lower_check), None)
    if key and not is_csit_query:  # Skip URL mapping for CSIT queries (already handled)
        url = URLS[key]
        # Ensure URL is within allowed MANUU bases; if not, try cached discovery
        if not is_allowed_manuu_url(url):
            url = get_cached_site_url(user_message)
        live_text = None
        try:
            live_text = fetch_from_web(url)
        except Exception:
            live_text = None

        if live_text:
            # Summarize using GPT and return structured reply
            try:
                summary = summarize_with_gpt(live_text, user_message)
                if summary and not summary.strip().startswith('[summarizer error]'):
                    return (summary, url)
            except Exception:
                pass

        # Live fetch failed: fallback to backup JSON
        try:
            if os.path.exists(BACKUP_PATH):
                with open(BACKUP_PATH, 'r', encoding='utf-8') as bf:
                    backup = _json.load(bf)
                if key in backup:
                    # Use summarizer to format backup data consistently
                    backup_content = backup.get(key, '')
                    formatted = summarize_with_gpt(backup_content, user_message)
                    return (formatted, None)
            # if no backup or key not present, continue to semantic RAG
        except Exception:
            pass
    # 2. Semantic search from MANUU data
    semantic_answer = semantic_search_response(user_message)
    if semantic_answer and not semantic_answer.startswith("Sorry, I could not find") and not semantic_answer.startswith("Please visit"):
            # Use the configured LLM (OpenAI) to summarize the chunk for a short, structured answer
        try:
            # Try to extract a link from the context chunk
            import re
            link_match = re.search(r'(https?://\S+)', semantic_answer)
            more_info = ''
            if link_match:
                more_info = f"\n\n➡️ For more information, visit: {link_match.group(1)}"
            # Build a single context string and call get_bot_reply which enforces
            # our structured response format and handles the "no data" fallback.
            full_context = semantic_answer + more_info
            try:
                llm_reply = get_bot_reply(user_message, context=full_context)
                # If helper returns an explicit LLM error, fall back to raw chunk
                if isinstance(llm_reply, str) and llm_reply.strip().startswith('[LLM error]'):
                    return semantic_answer
                # If helper returned the strict 'no data' fallback, forward that exact message
                if llm_reply.strip() == 'Sorry, I could not find that information in MANUU records.' or llm_reply.strip() == 'Please visit https://manuu.edu.in/ for the most updated information.':
                    return llm_reply
                # Validate reply against context to avoid hallucinations
                if not reply_matches_context(str(llm_reply), full_context):
                    print('[generate_response] LLM reply failed validation; falling back to semantic_answer')
                    return semantic_answer
                return llm_reply
            except Exception:
                return semantic_answer
        except Exception as e:
            # Fallback to raw chunk if Gemini fails
            return semantic_answer
    else:
        # Not found in embeddings/chunks — provide an approximate helpful answer with an official link
        try:
            fallback = manuu_fallback_url(user_message)
            um = user_message.lower()
            if 'exam' in um or 'exam date' in um or 'exam dates' in um or 'time table' in um or 'timetable' in um:
                title = 'Examination Information'
                bullets = [
                    'Exam timetables and results are posted on the official Examination page.',
                    f'Official Examination page: {fallback}',
                    'For exact dates, contact the Examination Cell or your department office.'
                ]
                return format_structured_reply(title, bullets)
            # Generic fallback to official MANUU page for Hyderabad campus
            # Use exact fallback message as per requirements
            return "Please visit https://manuu.edu.in/ for the most updated information."
        except Exception:
            # If anything fails, continue to LLM/default flow
            pass
    # 3. If not found, fallback to the LLM (OpenAI) or default
    use_llm = is_query_suitable_for_llm(user_message)
    if use_llm:
        # The system instructions in get_enhanced_response already enforce the MANUU chatbot behavior
        # Just pass the user query - the system prompt handles all the rules
        try:
            # For freeform queries, only call the LLM when we want it; do not call if
            # we don't have useful context. Use get_bot_reply with empty context
            # which will return an explicit 'no data' message if we intentionally
            # don't want to fetch external context.
            llm_reply = get_bot_reply(user_message, context="")
            if isinstance(llm_reply, str) and llm_reply.strip().startswith('[LLM error]'):
                err_text = llm_reply.lower()
                # If the error indicates quota problems, try a local semantic DB fallback
                if 'quota' in err_text or 'insufficient' in err_text:
                    try:
                        all_data = CollegeData.objects.all()
                        sem_resp = get_semantic_response(user_message, all_data)
                        if sem_resp:
                            return sem_resp
                        # If sem_resp is not available, validate the LLM reply against
                        # the prompt (we have no external context, so we only validate
                        # loosely) — this is conservative; if validation fails, return
                        # a friendly message instead.
                        if not reply_matches_context(str(llm_reply), user_message, threshold=0.05):
                            print('[generate_response] Freeform LLM reply failed light validation; returning friendly fallback')
                            return "The AI service is temporarily unavailable (quota). " + default_response()
                    except Exception:
                        pass
                    # Friendly notice when LLM is unavailable
                    return "The AI service is temporarily unavailable (quota). " + default_response()
                return default_response()
            return llm_reply
        except Exception:
            return default_response()
    # Final fallbacks: try rule-based and semantic DB lookups before default
    try:
        rb = rule_based_response(user_message)
        if rb:
            return rb
    except Exception:
        pass

    try:
        # Try category/semantic DB if available
        all_data = CollegeData.objects.all()
        sem_resp = get_semantic_response(user_message, all_data)
        if sem_resp:
            return sem_resp
    except Exception:
        pass

    # If we reach here and nothing matched or fetched, instruct user to check official site
    # Exact fallback message as per requirements
    return "Please visit https://manuu.edu.in/ for the most updated information."

def handle_quick_reply(user_message):
    """Handle predefined quick reply options.

    For key MANUU topics (Admission Process, Hostel Details, Canteen, Exam Dates),
    attempt a live fetch from the official website to provide current, detailed
    information. Falls back to static guidance text if live fetch fails.
    """
    # Try live fetch for the four Quick Actions first
    try:
        from utils.web_fetcher import fetch_from_web
        from utils.summarizer import summarize_with_gpt
        
        topic_url_map = {
            'admission process': 'https://manuu.edu.in/admissions',
            'admission': 'https://manuu.edu.in/admissions',
            'hostel details': 'https://manuu.edu.in/Hostels',
            'hostel': 'https://manuu.edu.in/Hostels',
            'hostels': 'https://manuu.edu.in/Hostels',
            'canteen': 'https://manuu.edu.in/Campus-Life',
            'library': 'https://manuu.edu.in/'
        }
        
        msg_key = user_message.lower().strip()
        
        # Check if the user query matches one of our dynamic topics
        matched_url = None
        for key, url in topic_url_map.items():
            if key in msg_key:
                matched_url = url
                break
                
        if matched_url:
            live_text = fetch_from_web(matched_url)
            if live_text:
                summary = summarize_with_gpt(live_text, user_message)
                if summary and not summary.strip().startswith('[summarizer error]'):
                    # Append source link
                    return f"{summary}\n\n➡️ For more information, visit: {matched_url}"
    except Exception as e:
        print(f"[handle_quick_reply] Live fetch failed: {e}")
        # Ignore live fetch errors and continue to static fallbacks
        pass
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

        'exam schedule': """Please contact the MANUU Examination Cell for accurate updates.""",

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

    # Add common quick-action keys used by the UI (exact matches)
    quick_replies.update({
    'canteen': """Canteen information:
- Canteen open on weekdays from morning to evening
- Offers a variety of North & South Indian dishes, snacks and beverages
- Separate timings for breakfast, lunch and evening snacks
Please ask if you want today's menu or exact timings.""",
    'hostel details': """Hostel Details (Hyderabad Campus):
- Separate hostels for male and female students
- Basic furnished rooms with shared mess
- 24x7 security and electricity backup
Contact the hostel office for allotment procedures.""",
    'exam dates': """Please contact the MANUU Examination Cell for accurate updates.""",
    'admission process': """Admission Process (Hyderabad Campus):
- Apply online via the official admissions portal
- Upload required documents and pay application fee
- Selection is merit or entrance-based depending on program
Visit the admissions page for application deadlines and forms."""
    })

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
        
        if similarities[best_match_index] > 20.:
            return all_data[best_match_index].answer
    except Exception as e:
        print(f"Semantic response error: {str(e)}")
    
    return None

def rule_based_response(user_message):
    lower_message = user_message.lower().strip()
    
    # Check exact match rules first
    if lower_message in ['hi', 'hello', 'hey', 'greetings', 'assalamualaikum', 'salam']:
        return "Hello! I am the official MANUU AI Assistant. How can I help you regarding Maulana Azad National Urdu University today?"
        
    if 'how it works' in lower_message or 'how do you work' in lower_message:
        return """### How the MANUU AI Assistant Works
I am an intelligent agent designed to help students and faculty navigate **Maulana Azad National Urdu University (MANUU)**. 

**Here is how I answer your questions:**
1. **Live Web Fetching**: When you ask about Admissions, Hostels, or CSIT Faculty, I fetch information *directly* from the official MANUU website in real-time.
2. **University Database**: For general queries, I perform a 'Semantic Search' across a vast, pre-loaded vector database containing MANUU course catalogs and events.
3. **AI Summarization**: Once I find the official source data, I synthesize it into a clean, easy-to-read format for you using the OpenAI GPT platform.

Ask me about "Hostels" or "CSIT Faculty" to see it in action!"""
        
    if 'who made you' in lower_message or 'who created you' in lower_message:
        return 'I was developed as a comprehensive intelligent system to assist students and staff at MANUU with official information and academic scheduling.'
        
    # Extract keywords from user message
    keywords = extract_keywords(user_message)
    
    # Map of keywords to categories
    category_keywords = {
        'admission': ['admission', 'apply', 'enrollment', 'register', 'joining', 'entrance', 'test', 'application', 'requirements', 'deadline', 'notification'],
        'exam': ['exam', 'test', 'schedule', 'result', 'grade', 'score', 'marks', 'semester', 'assessment', 'evaluation', 'timetable', 'date', 'internal', 'midterm', 'final'],
        'academic': ['class', 'lecture', 'timetable', 'schedule', 'course', 'subject', 'timing', 'period', 'semester', 'academic', 'study', 'department', 'school'],
        'facilities': ['facility', 'lab', 'laboratory', 'library', 'canteen', 'cafeteria', 'wifi', 'internet', 'computer', 'sports', 'gym', 'amenity'],
        'events': ['event', 'fest', 'festival', 'celebration', 'cultural', 'technical', 'workshop', 'seminar', 'conference', 'competition'],
        'club': ['club', 'society', 'association', 'committee', 'group', 'team', 'organization', 'activity', 'extracurricular'],
        'hostel': ['hostel', 'accommodation', 'stay', 'room', 'dormitory', 'residence', 'housing', 'facility', 'mess', 'fees', 'warden'],
        'faculty': ['faculty', 'professor', 'teacher', 'instructor', 'staff', 'lecturer', 'department', 'expert', 'specialist', 'hod', 'dean', 'principal'],
        'course': ['course', 'program', 'curriculum', 'syllabus', 'subject', 'study', 'branch', 'specialization', 'major', 'minor', 'credit'],
        'fee': ['fee', 'payment', 'tuition', 'cost', 'expense', 'scholarship', 'financial', 'aid', 'funding', 'loan', 'dues'],
        'placement': ['placement', 'job', 'career', 'recruitment', 'internship', 'employment', 'opportunity', 'company', 'interview', 'tpo', 'training'],
        'transport': ['transport', 'bus', 'vehicle', 'timing', 'route', 'pickup', 'drop', 'schedule', 'travel'],
        'contact': ['contact', 'phone', 'email', 'address', 'location', 'reach', 'enquiry', 'information', 'help', 'support', 'office']
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


