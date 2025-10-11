import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure secret key

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB in bytes
# ALLOWED_EXTENSIONS - removed to allow all file types

# Version Information
APP_VERSION = "1.4"
VERSION_HISTORY = {
    "1.0": "Initial release - Basic file upload functionality",
    "1.1": "Added health endpoint, original filename support, Docker configuration",
    "1.2": "Updated file size limit to 2GB for better browser compatibility",
    "1.3": "Added active state highlighting for navigation tabs",
    "1.4": "Fixed Admin tab to only highlight when active (not always red)"
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Admin credentials (password-only authentication)
# Password is read from environment variable ADMIN_PASSWORD
# If not set, defaults to 'admin123' (change this in production!)
ADMIN_PASSWORD_PLAIN = os.environ.get('ADMIN_PASSWORD', 'admin123')
if ADMIN_PASSWORD_PLAIN == 'admin123':
    print("⚠️  WARNING: Using default password! Set ADMIN_PASSWORD environment variable in production.")
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD_PLAIN)

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Brute force protection - store failed login attempts
login_attempts = {}  # {ip_address: {'count': int, 'locked_until': datetime}}

# Configuration for brute force protection
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 1

def allowed_file(filename):
    # Allow all file types - no restrictions
    return True

def get_file_size(filepath):
    """Get file size in human-readable format"""
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

@app.route('/')
def index():
    return render_template('index.html', version=APP_VERSION, version_history=VERSION_HISTORY)

@app.route('/health')
def health():
    """Simple health check endpoint for monitoring systems"""
    return f"OK v{APP_VERSION}"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        flash('No files selected', 'error')
        return redirect(url_for('index'))
    
    files = request.files.getlist('files')
    
    if not files or all(f.filename == '' for f in files):
        flash('No files selected', 'error')
        return redirect(url_for('index'))
    
    uploaded_count = 0
    failed_count = 0
    
    for file in files:
        if file and file.filename:
            # Use original filename (will overwrite if exists)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(filepath)
                uploaded_count += 1
            except Exception as e:
                failed_count += 1
                flash(f'Error uploading {filename}: {str(e)}', 'error')
    
    # Show summary message
    if uploaded_count > 0:
        if uploaded_count == 1:
            flash('1 file uploaded successfully!', 'success')
        else:
            flash(f'{uploaded_count} files uploaded successfully!', 'success')
    
    if failed_count > 0:
        if failed_count == 1:
            flash('1 file failed to upload', 'error')
        else:
            flash(f'{failed_count} files failed to upload', 'error')
    
    return redirect(url_for('index'))

def is_ip_locked(ip_address):
    """Check if IP is currently locked out"""
    if ip_address in login_attempts:
        attempt_info = login_attempts[ip_address]
        if 'locked_until' in attempt_info:
            if datetime.now() < attempt_info['locked_until']:
                return True, attempt_info['locked_until']
            else:
                # Lockout expired, reset
                del login_attempts[ip_address]
    return False, None

def record_failed_login(ip_address):
    """Record a failed login attempt"""
    if ip_address not in login_attempts:
        login_attempts[ip_address] = {'count': 0}
    
    login_attempts[ip_address]['count'] += 1
    
    if login_attempts[ip_address]['count'] >= MAX_LOGIN_ATTEMPTS:
        lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        login_attempts[ip_address]['locked_until'] = lockout_until
        return True, lockout_until
    
    return False, None

def reset_login_attempts(ip_address):
    """Clear login attempts after successful login"""
    if ip_address in login_attempts:
        del login_attempts[ip_address]

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    ip_address = request.remote_addr
    
    if request.method == 'POST':
        # Check if IP is locked
        is_locked, locked_until = is_ip_locked(ip_address)
        if is_locked:
            minutes_left = int((locked_until - datetime.now()).total_seconds() / 60) + 1
            flash(f'Too many failed attempts. Account locked for {minutes_left} more minute(s).', 'error')
            return render_template('admin_login.html')
        
        password = request.form.get('password')
        
        if password and check_password_hash(ADMIN_PASSWORD_HASH, password):
            # Successful login - reset attempts
            reset_login_attempts(ip_address)
            session['admin_logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_panel'))
        else:
            # Failed login - record attempt
            is_now_locked, lockout_until = record_failed_login(ip_address)
            
            if is_now_locked:
                flash(f'Too many failed attempts! Account locked for {LOCKOUT_DURATION_MINUTES} minutes.', 'error')
            else:
                attempts_left = MAX_LOGIN_ATTEMPTS - login_attempts[ip_address]['count']
                flash(f'Invalid password. {attempts_left} attempt(s) remaining.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin_logged_in'):
        flash('Please login first', 'error')
        return redirect(url_for('admin_login'))
    
    # Get all uploaded files
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            # Skip .gitkeep and other hidden files
            if os.path.isfile(filepath) and not filename.startswith('.'):
                files.append({
                    'name': filename,
                    'size': get_file_size(filepath),
                    'date': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    # Sort by date (newest first)
    files.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('admin_panel.html', files=files)

@app.route('/admin/download/<filename>')
def admin_download(filename):
    if not session.get('admin_logged_in'):
        flash('Please login first', 'error')
        return redirect(url_for('admin_login'))
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        flash('File not found', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/delete/<filename>')
def admin_delete(filename):
    if not session.get('admin_logged_in'):
        flash('Please login first', 'error')
        return redirect(url_for('admin_login'))
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            flash('File deleted successfully', 'success')
        else:
            flash('File not found', 'error')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large! Maximum file size is 2GB.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # For production, use a proper WSGI server like gunicorn
    app.run(debug=True, host='0.0.0.0', port=5000)

