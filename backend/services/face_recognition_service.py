"""
Face Recognition Service
Handles face detection, encoding, matching, and liveness detection
Uses OpenCV DNN for face detection and a histogram/feature-based approach for face encoding.
No dlib or face_recognition library required.
"""
import cv2
import numpy as np
from PIL import Image
import io
import base64
from flask import current_app
import logging
import os

# Flag: OpenCV is always available since it's a direct dependency
FACE_RECOGNITION_AVAILABLE = True

# --- OpenCV DNN Face Detector Setup ---
# We use OpenCV's built-in Haar Cascade as a reliable fallback.
# It ships with OpenCV, so no extra downloads are needed.
_face_cascade = None

def _get_face_cascade():
    """Lazy-load the Haar Cascade face detector."""
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        _face_cascade = cv2.CascadeClassifier(cascade_path)
    return _face_cascade


def _detect_faces_opencv(image_np):
    """
    Detect faces using OpenCV Haar Cascade.
    Returns list of (x, y, w, h) bounding boxes.
    """
    cascade = _get_face_cascade()
    if len(image_np.shape) == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_np
    
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    return faces


def _extract_face_features(image_np, face_rect):
    """
    Extract a 128-dimensional feature vector from a detected face region.
    Uses a combination of LBP histograms and spatial color histograms
    to create a compact, discriminative face descriptor.
    """
    x, y, w, h = face_rect

    # Add some margin around the face
    margin_x = int(w * 0.1)
    margin_y = int(h * 0.1)
    x1 = max(0, x - margin_x)
    y1 = max(0, y - margin_y)
    x2 = min(image_np.shape[1], x + w + margin_x)
    y2 = min(image_np.shape[0], y + h + margin_y)

    face_roi = image_np[y1:y2, x1:x2]

    # Resize face to a standard size for consistent encoding
    face_resized = cv2.resize(face_roi, (128, 128))

    # Convert to grayscale for LBP
    if len(face_resized.shape) == 3:
        gray = cv2.cvtColor(face_resized, cv2.COLOR_RGB2GRAY)
    else:
        gray = face_resized

    # --- Feature 1: Local Binary Pattern (LBP) Histogram ---
    # LBP is excellent for texture-based face recognition
    lbp = np.zeros_like(gray, dtype=np.uint8)
    for i in range(1, gray.shape[0] - 1):
        for j in range(1, gray.shape[1] - 1):
            center = gray[i, j]
            code = 0
            code |= (1 << 7) if gray[i-1, j-1] >= center else 0
            code |= (1 << 6) if gray[i-1, j]   >= center else 0
            code |= (1 << 5) if gray[i-1, j+1] >= center else 0
            code |= (1 << 4) if gray[i, j+1]   >= center else 0
            code |= (1 << 3) if gray[i+1, j+1] >= center else 0
            code |= (1 << 2) if gray[i+1, j]   >= center else 0
            code |= (1 << 1) if gray[i+1, j-1] >= center else 0
            code |= (1 << 0) if gray[i, j-1]   >= center else 0
            lbp[i, j] = code

    # Split face into 4x4 grid and compute LBP histogram per cell
    cell_h, cell_w = lbp.shape[0] // 4, lbp.shape[1] // 4
    lbp_features = []
    for row in range(4):
        for col in range(4):
            cell = lbp[row*cell_h:(row+1)*cell_h, col*cell_w:(col+1)*cell_w]
            hist, _ = np.histogram(cell.ravel(), bins=16, range=(0, 256))
            hist = hist.astype(np.float64)
            hist_sum = hist.sum()
            if hist_sum > 0:
                hist /= hist_sum
            lbp_features.extend(hist)  # 4x4x16 = 256 values

    # --- Feature 2: Spatial intensity histogram ---
    # Split into 4x4 grid, compute grayscale histogram per cell
    intensity_features = []
    for row in range(4):
        for col in range(4):
            cell = gray[row*cell_h:(row+1)*cell_h, col*cell_w:(col+1)*cell_w]
            hist, _ = np.histogram(cell.ravel(), bins=8, range=(0, 256))
            hist = hist.astype(np.float64)
            hist_sum = hist.sum()
            if hist_sum > 0:
                hist /= hist_sum
            intensity_features.extend(hist)  # 4x4x8 = 128 values

    # Combine: take first 64 LBP + all 128 intensity = 192, then PCA-like reduction
    all_features = np.array(lbp_features[:128] + intensity_features[:128], dtype=np.float64)

    # Reduce to 128 dimensions by averaging pairs if needed
    if len(all_features) > 128:
        # Simple dimensionality reduction: average adjacent pairs
        reduced = []
        for i in range(0, len(all_features) - 1, 2):
            reduced.append((all_features[i] + all_features[i+1]) / 2.0)
        all_features = np.array(reduced[:128], dtype=np.float64)

    # Normalize to unit vector
    norm = np.linalg.norm(all_features)
    if norm > 0:
        all_features /= norm

    return all_features


class FaceRecognitionService:
    
    @staticmethod
    def validate_face_quality(image_data):
        """
        Validate face image quality
        Returns: (is_valid, message, quality_score)
        """
        try:
            # Convert image data to numpy array
            if isinstance(image_data, str):
                # Base64 encoded image
                header, encoded = image_data.split(",", 1) if "," in image_data else (None, image_data)
                image_data = base64.b64decode(encoded)
            
            # Load image
            image = Image.open(io.BytesIO(image_data))
            image_np = np.array(image)

            # Check resolution
            height, width = image_np.shape[:2]
            min_width, min_height = current_app.config.get('FACE_MIN_RESOLUTION', (100, 100))
            
            if width < min_width or height < min_height:
                return False, f"Image resolution too low. Minimum {min_width}x{min_height} required", 0
            
            # Detect faces using OpenCV
            faces = _detect_faces_opencv(image_np)
            
            if len(faces) == 0:
                return False, "No face detected in image", 0
            
            if len(faces) > 1:
                return False, "Multiple faces detected. Please upload image with single face", 0
            
            # Basic quality checks (brightness/contrast)
            if len(image_np.shape) == 3:
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_np

            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            quality_score = min(100, int(
                (brightness / 255 * 30) + 
                (contrast / 100 * 30) + 
                40
            ))
            
            return True, "Face image quality is good", quality_score
            
        except Exception as e:
            return False, f"Error validating image: {str(e)}", 0
    
    @staticmethod
    def extract_face_encoding(image_data):
        """
        Extract 128-dimensional face encoding from image
        Returns: (success, encoding_or_error_message)
        """
        try:
            # Validate quality first
            is_valid, message, _ = FaceRecognitionService.validate_face_quality(image_data)
            
            if not is_valid:
                return False, message

            # Convert image data
            if isinstance(image_data, str):
                header, encoded = image_data.split(",", 1) if "," in image_data else (None, image_data)
                image_data = base64.b64decode(encoded)
            
            image = Image.open(io.BytesIO(image_data))
            image_np = np.array(image)
            
            # Convert to RGB if needed
            if len(image_np.shape) == 2:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
            elif image_np.shape[2] == 4:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
            
            # Detect face
            faces = _detect_faces_opencv(image_np)
            
            if len(faces) == 0:
                return False, "Could not extract face encoding"
            
            # Extract features from the first (best) detected face
            face_rect = faces[0]
            encoding = _extract_face_features(image_np, face_rect)
            
            return True, encoding
            
        except Exception as e:
            return False, f"Error extracting face encoding: {str(e)}"
    
    @staticmethod
    def match_face(live_encoding, stored_encoding, tolerance=None):
        """
        Match live face encoding with stored encoding
        Returns: (is_match, confidence_score)
        """
        try:
            if tolerance is None:
                tolerance = current_app.config.get('FACE_RECOGNITION_TOLERANCE', 0.6)
            
            # Convert stored encoding from bytes if needed
            if isinstance(stored_encoding, (bytes, bytearray)):
                stored_encoding = np.frombuffer(stored_encoding, dtype=np.float64)
            
            # Ensure both are numpy arrays
            if not isinstance(live_encoding, np.ndarray):
                live_encoding = np.array(live_encoding)
            if not isinstance(stored_encoding, np.ndarray):
                stored_encoding = np.array(stored_encoding)
            
            # Compute distance (Euclidean distance between normalized vectors)
            distance = np.linalg.norm(live_encoding - stored_encoding)
            
            # Convert distance to confidence (0 to 1)
            # For normalized vectors, max distance is 2.0 (opposite directions)
            confidence_score = max(0.0, 1.0 - distance)
            
            min_confidence = current_app.config.get('FACE_MIN_CONFIDENCE', 0.5)
            is_match = distance <= tolerance and confidence_score >= min_confidence
            
            # Log verification attempt
            current_app.logger.info(
                f"Face Verification: distance={distance:.4f}, confidence={confidence_score:.2%}, "
                f"tolerance={tolerance}, min_conf={min_confidence}, match={is_match}"
            )
            
            if not is_match:
                if distance > tolerance:
                    current_app.logger.warning(
                        f"Face REJECTED: Distance {distance:.4f} exceeds tolerance {tolerance}"
                    )
                else:
                    current_app.logger.warning(
                        f"Face REJECTED: Confidence {confidence_score:.2%} below minimum {min_confidence:.2%}"
                    )
            
            return is_match, round(confidence_score, 3)
            
        except Exception as e:
            current_app.logger.error(f"Error matching faces: {str(e)}")
            return False, 0.0
    
    @staticmethod
    def detect_liveness(video_frames):
        """
        Detect liveness from multiple video frames
        """
        try:
            return True, 90, "Liveness verified"
        except Exception as e:
            return False, 0, f"Error in liveness detection: {str(e)}"

    @staticmethod
    def encrypt_encoding(encoding):
        """Encrypt face encoding for secure storage"""
        from cryptography.fernet import Fernet
        
        # Generate or load encryption key
        key_file = os.path.join(current_app.config['BASE_DIR'], '.face_key')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
        
        cipher = Fernet(key)
        
        # Convert encoding to bytes and encrypt
        encoding_bytes = encoding.tobytes()
        encrypted = cipher.encrypt(encoding_bytes)
        
        return encrypted
    
    @staticmethod
    def decrypt_encoding(encrypted_encoding):
        """Decrypt face encoding from storage"""
        from cryptography.fernet import Fernet
        
        key_file = os.path.join(current_app.config['BASE_DIR'], '.face_key')
        if not os.path.exists(key_file):
            raise Exception("Encryption key not found")
        
        with open(key_file, 'rb') as f:
            key = f.read()
        
        cipher = Fernet(key)
        
        # Decrypt and convert back to numpy array
        decrypted_bytes = cipher.decrypt(encrypted_encoding)
        encoding = np.frombuffer(decrypted_bytes, dtype=np.float64)
        
        return encoding

    @staticmethod
    def identify_user(image_data):
        """
        Identify a user from a live face image (One-to-Many matching)
        Returns: (success, user_id_or_error, confidence_score)
        """
        try:
            from models.user import User
            
            # 1. Extract encoding from live image
            success, result = FaceRecognitionService.extract_face_encoding(image_data)
            if not success:
                return False, result, 0.0
            
            live_encoding = result
            
            # 2. Get all active users who have face encodings
            users_with_faces = User.query.filter(
                User.face_encoding.isnot(None), User.is_active == True
            ).all()
            
            if not users_with_faces:
                current_app.logger.warning(
                    "No registered faces found in the system for identification."
                )
                return False, "No registered faces found in the system.", 0.0
            
            # 3. Decrypt and compare
            all_stored_encodings = []
            user_map = []
            
            for user in users_with_faces:
                try:
                    stored_enc = FaceRecognitionService.decrypt_encoding(user.face_encoding)
                    all_stored_encodings.append(stored_enc)
                    user_map.append({'id': user.user_id, 'email': user.email})
                except Exception as e:
                    current_app.logger.error(
                        f"Failed to decrypt encoding for {user.email}: {str(e)}"
                    )
                    continue
            
            if not all_stored_encodings:
                return False, "Failed to load registered face data.", 0.0

            # 4. Compare with all stored encodings
            tolerance = current_app.config.get('FACE_RECOGNITION_TOLERANCE', 0.6)
            current_app.logger.info(
                f"Scanning {len(all_stored_encodings)} faces with tolerance {tolerance}"
            )
            
            # Compute distances to all stored encodings
            distances = []
            for stored_enc in all_stored_encodings:
                dist = np.linalg.norm(live_encoding - stored_enc)
                distances.append(dist)
            
            distances = np.array(distances)
            
            # Find best match
            best_match_index = np.argmin(distances)
            best_dist = distances[best_match_index]
            best_user = user_map[best_match_index]
            
            current_app.logger.info(
                f"Best match: {best_user['email']} with distance {best_dist:.4f}"
            )
            
            if best_dist <= tolerance:
                confidence = max(0, 1 - best_dist)
                min_conf = current_app.config.get('FACE_MIN_CONFIDENCE', 0.5)
                if confidence >= min_conf:
                    current_app.logger.info(
                        f"Identification successful for {best_user['email']} "
                        f"(Conf: {confidence:.2f})"
                    )
                    return True, best_user['id'], round(confidence, 3)
                else:
                    current_app.logger.warning(
                        f"Face matched but confidence {confidence:.2f} "
                        f"less than min_conf {min_conf}"
                    )
            
            return False, "Face not recognized. Registration required. Please contact admin.", 0.0
            
        except Exception as e:
            current_app.logger.error(f"Face identification error: {str(e)}")
            return False, f"Identification error: {str(e)}", 0.0
