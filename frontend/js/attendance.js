/**
 * Enhanced Kiosk Mode Attendance Logic
 * Two-step verification: Enter ID → Verify Face
 */

const API_BASE = window.location.origin.includes('http') ? window.location.origin : 'http://localhost:5000';
const API_URL = API_BASE + '/api/public';
let kioskStream = null;
let currentUser = null;

function showAttendanceKiosk() {
    const modal = document.getElementById('kiosk-modal');
    modal.style.display = 'flex';
    resetKioskFlow();
}

function hideAttendanceKiosk() {
    const modal = document.getElementById('kiosk-modal');
    modal.style.display = 'none';
    stopKioskCamera();
    resetKioskFlow();
}

function resetKioskFlow() {
    currentUser = null;
    document.getElementById('id-input-step').style.display = 'block';
    document.getElementById('verification-step').style.display = 'none';
    document.getElementById('student-id-input').value = '';
    document.getElementById('kiosk-status').textContent = 'Enter your Student ID to begin';
}

async function submitStudentId() {
    const studentId = document.getElementById('student-id-input').value.trim();
    const status = document.getElementById('kiosk-status');
    const submitBtn = document.getElementById('submit-id-btn');

    if (!studentId) {
        showKioskToast('Please enter your Student ID', 'error');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class=\"fas fa-spinner fa-spin\"></i> Checking...';
    status.textContent = 'Looking up your profile...';

    try {
        const response = await fetch(`${API_URL}/user/${studentId}`);
        const result = await response.json();

        if (response.ok) {
            currentUser = result;
            // Show user profile
            const idLabel = result.role === 'staff' ? 'Staff ID' : 'Student ID';
            document.getElementById('user-name-display').textContent = result.name;
            document.getElementById('user-email-display').textContent = result.email;
            document.getElementById('user-id-display').textContent = `${idLabel}: ${result.display_id}`;

            // Switch to verification step
            document.getElementById('id-input-step').style.display = 'none';
            document.getElementById('verification-step').style.display = 'block';
            status.textContent = 'Profile loaded. Please look at the camera.';

            // Start camera
            await startKioskCamera();
        } else {
            status.innerHTML = `<span style=\"color: var(--danger)\">${result.error}</span>`;
            showKioskToast(result.error, 'error');
        }
    } catch (err) {
        console.error('ID lookup error:', err);
        status.textContent = 'System error. Please try again.';
        showKioskToast('Failed to verify ID', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class=\"fas fa-arrow-right\"></i> Continue';
    }
}

async function startKioskCamera() {
    try {
        const video = document.getElementById('kiosk-video');
        kioskStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }
        });
        video.srcObject = kioskStream;
    } catch (err) {
        console.error('Camera Error:', err);
        showKioskToast('Unable to access camera', 'error');
    }
}

function stopKioskCamera() {
    if (kioskStream) {
        kioskStream.getTracks().forEach(track => track.stop());
        kioskStream = null;
    }
}

function showKioskToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'glass-card mb-2 p-3 fade-in';
    toast.style.minWidth = '250px';
    toast.style.borderLeft = `4px solid ${type === 'success' ? 'var(--success)' : 'var(--danger)'}`;

    const icon = type === 'success' ? 'check-circle' : 'exclamation-circle';
    const color = type === 'success' ? 'var(--success)' : 'var(--danger)';

    toast.innerHTML = `
        <div class=\"flex items-center gap-3\">
            <i class=\"fas fa-${icon}\" style=\"color: ${color}; font-size: 1.2rem;\"></i>
            <span>${message}</span>
        </div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

async function captureAndVerify() {
    if (!currentUser) {
        showKioskToast('No user selected', 'error');
        return;
    }

    const video = document.getElementById('kiosk-video');
    const canvas = document.getElementById('kiosk-canvas');
    const status = document.getElementById('kiosk-status');
    const btn = document.getElementById('kiosk-capture-btn');

    if (!kioskStream) return;

    // UI Feedback
    btn.disabled = true;
    btn.innerHTML = '<i class=\"fas fa-spinner fa-spin\"></i> Verifying...';
    status.textContent = 'Comparing faces...';

    try {
        // Capture frame
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        const imageData = canvas.toDataURL('image/jpeg', 0.8);

        // Get Geo Location
        let geo = null;
        try {
            const pos = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
            });
            geo = `${pos.coords.latitude},${pos.coords.longitude}`;
        } catch (e) { console.warn('Geolocation failed or denied'); }

        // Send to API
        const response = await fetch(`${API_URL}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                face_image: imageData,
                geo_location: geo
            })
        });

        const result = await response.json();

        if (response.ok) {
            status.innerHTML = `<span style=\"color: var(--success)\">✓ ${result.message}</span>`;
            showKioskToast(result.message, 'success');
            // Hide after a short delay
            setTimeout(hideAttendanceKiosk, 2500);
        } else {
            status.innerHTML = `<span style=\"color: var(--danger)\">✗ ${result.error}</span>`;
            showKioskToast(result.error, 'error');
        }
    } catch (err) {
        console.error('Verify Error:', err);
        status.textContent = 'System error. Try again.';
        showKioskToast('Verification failed', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class=\"fas fa-camera\"></i> Verify Face';
    }
}

// Allow Enter key to submit ID
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('student-id-input');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') submitStudentId();
        });
    }
});
