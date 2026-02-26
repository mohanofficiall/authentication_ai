"""
Chatbot Routes
Handles chatbot interactions (Mock Rasa integration)
"""
from flask import Blueprint, request, jsonify, current_app
from utils.jwt_handler import token_required
from services.attendance_service import AttendanceService, SessionService
from models.user import User
from models.attendance import Attendance
from datetime import date
import random
import requests
import json

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@chatbot_bp.route('/message', methods=['POST'])
@token_required
def handle_message():
    """Handle chatbot message using OpenRouter API"""
    try:
        user_id = request.current_user['user_id']
        role = request.current_user['role']
        user_name = request.current_user.get('name', 'User')
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        # Get system configuration
        api_key = current_app.config.get('OPENROUTER_API_KEY')
        model = current_app.config.get('OPENROUTER_MODEL')
        
        if not api_key or api_key == 'YOUR_OPENROUTER_API_KEY':
            return jsonify({
                'response': [{'text': "⚠️ OpenRouter API Key not configured. Please contact the administrator."}]
            }), 200

        # Prepare system prompt for context
        attendance_info = ""
        if role == 'student':
            percent = AttendanceService.calculate_attendance_percentage(user_id)
            today = AttendanceService.get_today_status(user_id)
            attendance_info = f"\n- Your current attendance: {percent}%.\n- Today's status: {'Present' if today['marked'] else 'Not marked yet'}."

        system_prompt = f"""You are 'Attendo AI', a helpful and intelligent school assistant.
Current User: {user_name} ({role.capitalize()})
{attendance_info}

Instructions:
1. Provide clear and concise answers to student/staff questions.
2. You can handle ANY subject-related doubts (Math, Science, History, Coding, etc.) just like ChatGPT.
3. For attendance-related questions, use the provided context above.
4. If asked about how to use the system:
   - Students mark attendance via 'Mark Attendance' on their dashboard.
   - Staff start sessions via 'Start New Session'.
5. Be professional, friendly, and encouraging.
"""

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            }),
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            bot_text = result['choices'][0]['message']['content']
            return jsonify({'response': [{'text': bot_text}]}), 200
        else:
            current_app.logger.error(f"OpenRouter Error: {response.text}")
            return jsonify({'error': 'AI service currently unavailable'}), 503
            
    except Exception as e:
        current_app.logger.error(f"Chatbot error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
