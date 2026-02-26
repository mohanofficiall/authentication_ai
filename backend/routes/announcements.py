from flask import Blueprint, request, jsonify, current_app
from models.announcement import Announcement
from database.db import db
from utils.jwt_handler import token_required, role_required
import uuid

announcements_bp = Blueprint('announcements', __name__, url_prefix='/api/announcements')

@announcements_bp.route('', methods=['GET'])
@token_required
def get_announcements():
    """Get all announcements"""
    try:
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
        return jsonify({
            'announcements': [a.to_dict() for a in announcements]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Get announcements error: {str(e)}")
        return jsonify({'error': 'Failed to fetch announcements'}), 500

@announcements_bp.route('', methods=['POST'])
@token_required
@role_required(['staff', 'admin'])
def create_announcement():
    """Create a new announcement"""
    try:
        data = request.get_json()
        user_id = request.current_user['user_id']
        
        if not data.get('title') or not data.get('content'):
            return jsonify({'error': 'Title and content are required'}), 400
            
        new_announcement = Announcement(
            announcement_id=str(uuid.uuid4()),
            author_id=user_id,
            title=data['title'],
            content=data['content'],
            type=data.get('type', 'general')
        )
        
        db.session.add(new_announcement)
        db.session.commit()
        
        return jsonify({
            'message': 'Announcement created successfully',
            'announcement': new_announcement.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create announcement error: {str(e)}")
        return jsonify({'error': 'Failed to create announcement'}), 500

@announcements_bp.route('/<id>', methods=['DELETE'])
@token_required
@role_required(['staff', 'admin'])
def delete_announcement(id):
    """Delete an announcement"""
    try:
        announcement = Announcement.query.get(id)
        if not announcement:
            return jsonify({'error': 'Announcement not found'}), 404
            
        # Optional: Check if the user is the author or an admin
        user_id = request.current_user['user_id']
        role = request.current_user['role']
        
        if role != 'admin' and announcement.author_id != user_id:
            return jsonify({'error': 'Unauthorized to delete this announcement'}), 403
            
        db.session.delete(announcement)
        db.session.commit()
        
        return jsonify({'message': 'Announcement deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete announcement error: {str(e)}")
        return jsonify({'error': 'Failed to delete announcement'}), 500
