from flask import Blueprint, request, jsonify, current_app, send_from_directory
from utils.jwt_handler import token_required, role_required
from models.document import Document
from database.db import db
from utils.logger import log_action
import os
import uuid
from werkzeug.utils import secure_filename

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@documents_bp.route('/upload', methods=['POST'])
@token_required
@role_required(['staff', 'admin'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Generate a unique filename to avoid collisions
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            upload_folder = current_app.config['UPLOAD_FOLDER']
            documents_folder = os.path.join(upload_folder, 'documents')
            os.makedirs(documents_folder, exist_ok=True)
            
            file_path = os.path.join(documents_folder, unique_filename)
            file.save(file_path)
            
            # Save to database
            document_id = str(uuid.uuid4())
            uploader_id = request.current_user['user_id']
            
            # Additional info from form
            title = request.form.get('title', filename)
            description = request.form.get('description', '')
            subject = request.form.get('subject', '')
            
            new_doc = Document(
                document_id=document_id,
                uploader_id=uploader_id,
                filename=filename,
                file_path=os.path.join('documents', unique_filename), # Relative path for serving
                file_type=filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown',
                title=title,
                description=description,
                subject=subject
            )
            
            db.session.add(new_doc)
            db.session.commit()
            
            log_action(uploader_id, 'upload_document', 'success', f'Uploaded {filename}')
            
            return jsonify({
                'message': 'Document uploaded successfully',
                'document': new_doc.to_dict()
            }), 201
            
        return jsonify({'error': 'File type not allowed'}), 400
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Failed to upload document'}), 500

@documents_bp.route('', methods=['GET'])
@token_required
def get_documents():
    try:
        documents = Document.query.order_by(Document.created_at.desc()).all()
        return jsonify({
            'documents': [doc.to_dict() for doc in documents]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Get documents error: {str(e)}")
        return jsonify({'error': 'Failed to fetch documents'}), 500

@documents_bp.route('/download/<document_id>', methods=['GET'])
@token_required
def download_document(document_id):
    try:
        doc = Document.query.get(document_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        # doc.file_path is relative to UPLOAD_FOLDER (e.g., 'documents/uuid_name.pdf')
        directory = os.path.dirname(os.path.join(upload_folder, doc.file_path))
        filename = os.path.basename(doc.file_path)
        
        return send_from_directory(directory, filename, as_attachment=True, download_name=doc.filename)
        
    except Exception as e:
        current_app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Failed to download document'}), 500

@documents_bp.route('/<document_id>', methods=['DELETE'])
@token_required
@role_required(['staff', 'admin'])
def delete_document(document_id):
    try:
        doc = Document.query.get(document_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check if uploader is the current user (only staff can delete their own, admin can delete any)
        if request.current_user['role'] == 'staff' and doc.uploader_id != request.current_user['user_id']:
            return jsonify({'error': 'Insufficient permissions to delete this document'}), 403
            
        # Delete file
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, doc.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        db.session.delete(doc)
        db.session.commit()
        
        log_action(request.current_user['user_id'], 'delete_document', 'success', f'Deleted {doc.filename}')
        
        return jsonify({'message': 'Document deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete error: {str(e)}")
        return jsonify({'error': 'Failed to delete document'}), 500
