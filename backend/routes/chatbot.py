"""
Chatbot Routes - Lite Edition (No DLL dependencies)
Handles chatbot interactions with internal intelligence and Wikipedia search.
"""
from flask import Blueprint, request, jsonify, current_app
from utils.jwt_handler import token_required
from services.attendance_service import AttendanceService
import requests
import json
import random
import re

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

def get_wiki_summary(query):
    """Fetch a summary from Wikipedia for study help"""
    # Clean query: strip punctuation
    query = re.sub(r'[?.,!]' , '', query).strip()
    
    headers = {
        'User-Agent': 'AttendoAIChatbot/1.0 (contact: mohan@example.com) requests/2.31'
    }
    
    try:
        # 1. Search for page
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "utf8": 1,
            "srlimit": 1
        }
        r = requests.get(search_url, params=params, headers=headers, timeout=5)
        search_data = r.json()
        
        if search_data.get('query', {}).get('search'):
            title = search_data['query']['search'][0]['title']
            
            # 2. Get extract
            extract_params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "redirects": 1
            }
            r = requests.get(search_url, params=extract_params, headers=headers, timeout=5)
            pages = r.json().get('query', {}).get('pages', {})
            for page_id in pages:
                extract = pages[page_id].get('extract', '')
                if extract:
                    # Clean up and shorten
                    sentences = extract.split('. ')
                    summary = '. '.join(sentences[:3]) + '.'
                    return f"**{title}**\n\n{summary}\n\n(Source: Wikipedia)"
    except Exception:
        pass
    return None

def get_local_knowledge(user_id, role, message):
    """Handle attendance and basic greetings locally"""
    msg = message.lower()
    
    # Personal Status
    if any(k in msg for k in ['my attendance', 'percentage', 'status', 'how much']):
        if role == 'student' and user_id:
            p = AttendanceService.calculate_attendance_percentage(user_id)
            today = AttendanceService.get_today_status(user_id)
            s = "Present" if today['marked'] else "Not marked yet"
            return f"Your current attendance is **{p}%**. Today's status: **{s}**."
        return "You can check attendance percentages in the student dashboard or analytics panel."

    # System Instructions
    if any(k in msg for k in ['how', 'mark', 'capture', 'recogni', 'camera', 'photo', 'face']):
        return "To mark attendance: Go to the 'Mark Attendance' page, allow camera access, and look at the screen. We use AI to verify your face and ensure you are present!"

    # Study keywords
    study_keywords = ['what is', 'define', 'explain', 'tell me', 'who is', 'where is', 'how does', 'history', 'science', 'math', 'about']
    if any(k in msg for k in study_keywords):
        # Clean query
        query = message
        clean_msg = re.sub(r'^(what is|tell me about|who is|define|explain|about|tell me)\s+', '', msg, flags=re.IGNORECASE).strip()
        if clean_msg:
            wiki = get_wiki_summary(clean_msg)
            if wiki:
                return wiki

    return None

@chatbot_bp.route('/message', methods=['POST'])
def handle_message():
    try:
        # Try to identify user if token exists
        user = {}
        if 'Authorization' in request.headers:
            try:
                auth_header = request.headers['Authorization']
                token = auth_header.split(' ')[1]
                from utils.jwt_handler import decode_token
                payload = decode_token(token)
                if 'error' not in payload:
                    user = payload
            except: pass

        user_id = user.get('user_id')
        role = user.get('role', 'guest')
        user_name = user.get('name', 'User')
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        # 1. Try Local/Wiki Knowledge
        reply = get_local_knowledge(user_id, role, user_message)
        if reply:
            return jsonify({'response': [{'text': reply}]}), 200

        # 2. Try OpenRouter (if enabled)
        api_key = current_app.config.get('OPENROUTER_API_KEY')
        if api_key and api_key != 'YOUR_OPENROUTER_API_KEY':
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    data=json.dumps({
                        "model": current_app.config.get('OPENROUTER_MODEL', 'meta-llama/llama-3-8b-instruct:free'),
                        "messages": [{"role": "user", "content": user_message}]
                    }),
                    timeout=5
                )
                if response.status_code == 200:
                    return jsonify({'response': [{'text': response.json()['choices'][0]['message']['content']}]}), 200
            except:
                pass

        # 3. Default
        greet = [
            f"Hello {user_name}! Ask me about your studies (e.g., 'What is gravity?') or your attendance.",
            "I'm Attendo AI. I can help with study doubts and system info!",
            "Need help with your subjects? Just ask me!"
        ]
        return jsonify({'response': [{'text': random.choice(greet)}]}), 200

    except Exception as e:
        return jsonify({'response': [{'text': "I'm processing your request. Please ask simple study questions!"}]}), 200
