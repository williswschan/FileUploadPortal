import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure secret key

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB in bytes
# ALLOWED_EXTENSIONS - removed to allow all file types

# Version Information
APP_VERSION = "1.6"
VERSION_HISTORY = {
    "1.0": "Initial release - Basic file upload functionality",
    "1.1": "Added health endpoint, original filename support, Docker configuration",
    "1.2": "Updated file size limit to 2GB for better browser compatibility",
    "1.3": "Added active state highlighting for navigation tabs",
    "1.4": "Fixed Admin tab to only highlight when active (not always red)",
    "1.5": "Added email notification system for file uploads",
    "1.6": "Added Signal messaging notification for file uploads"
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

# Email notification configuration
EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT')
SMTP_SERVER = os.environ.get('SMTP_SERVER')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '25'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

# Check if email notification is configured (SMTP_USERNAME and SMTP_PASSWORD are optional)
EMAIL_ENABLED = all([EMAIL_SENDER, EMAIL_RECIPIENT, SMTP_SERVER])
if EMAIL_ENABLED:
    print("✅ Email notifications enabled")
else:
    print("ℹ️  Email notifications disabled (missing environment variables)")

# Signal notification configuration
SIGNAL_API_URL = os.environ.get('SIGNAL_API_URL')
SIGNAL_NUMBER = os.environ.get('SIGNAL_NUMBER')
SIGNAL_RECIPIENT = os.environ.get('SIGNAL_RECIPIENT')

# Signal is enabled only if all environment variables are set
SIGNAL_ENABLED = all([SIGNAL_API_URL, SIGNAL_NUMBER, SIGNAL_RECIPIENT])
if SIGNAL_ENABLED:
    print(f"✅ Signal notifications enabled - sending to {SIGNAL_RECIPIENT}")
else:
    print("ℹ️  Signal notifications disabled (missing environment variables)")

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

def send_upload_notification(uploaded_files, client_ip):
    """Send email notification when files are uploaded"""
    if not EMAIL_ENABLED:
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECIPIENT
        msg['Subject'] = f"📁 File Upload Notification - {len(uploaded_files)} file(s) uploaded"
        
        # Create email body
        body = f"""
Hello,

A file upload has been completed on the MYMSNGROUP File Upload Portal.

📊 Upload Details:
• Number of files: {len(uploaded_files)}
• Upload time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Client IP: {client_ip}
• Portal version: {APP_VERSION}

📋 Uploaded Files:
"""
        
        for i, file_info in enumerate(uploaded_files, 1):
            body += f"  {i}. {file_info['name']} ({file_info['size']})\n"
        
        body += f"""
🔗 Access the admin panel to view and manage these files.

Best regards,
MYMSNGROUP File Upload Portal
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        
        # Only use TLS and authentication if credentials are provided
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, text)
        server.quit()
        
        print(f"✅ Email notification sent to {EMAIL_RECIPIENT}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email notification: {str(e)}")
        return False

def send_signal_msg(message):
    """
    Send Signal notification via Signal API
    Revised Signal notification function with proper success detection
    """
    if not SIGNAL_ENABLED:
        return False
    
    try:
        url = SIGNAL_API_URL
        recipients = [SIGNAL_RECIPIENT]
        number = SIGNAL_NUMBER
        message = str(message)
        message = message.replace('"', '\\"')
        headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
        payload = '{"message": "%s", "number": "%s", "recipients": ["%s"]}' % (message, number, recipients[0])

        response = requests.post(url, data=payload.encode(), headers=headers)
        print(f"Signal API Response Status: {response.status_code}")
        print(f"Signal API Response: {response.text}")
        
        # KEY FIX: Status 201 means success in HTTP!
        if response.status_code in [200, 201]:
            print("✅ Signal message sent successfully!")
            return True
        else:
            print("❌ Failed to send Signal message")
            return False
            
    except Exception as e:
        print(f"❌ Signal Exception: {e}")
        return False

def send_upload_signal_notification(uploaded_files, client_ip):
    """Send Signal notification when files are uploaded"""
    if not SIGNAL_ENABLED:
        return False
    
    try:
        # Create Signal message
        message = f"📁 File Upload Notification\n\n"
        message += f"Number of files: {len(uploaded_files)}\n"
        message += f"Upload time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"Client IP: {client_ip}\n"
        message += f"Portal version: {APP_VERSION}\n\n"
        message += f"Uploaded Files:\n"
        
        for i, file_info in enumerate(uploaded_files, 1):
            message += f"  {i}. {file_info['name']} ({file_info['size']})\n"
        
        message += f"\nMYMSNGROUP File Upload Portal"
        
        # Send Signal message
        return send_signal_msg(message)
        
    except Exception as e:
        print(f"❌ Failed to send Signal notification: {str(e)}")
        return False

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
    uploaded_files = []  # Store info about successfully uploaded files
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'Unknown'))
    
    for file in files:
        if file and file.filename:
            # Use original filename (will overwrite if exists)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(filepath)
                uploaded_count += 1
                # Store file info for email notification
                uploaded_files.append({
                    'name': filename,
                    'size': get_file_size(filepath)
                })
            except Exception as e:
                failed_count += 1
                flash(f'Error uploading {filename}: {str(e)}', 'error')
    
    # Send email notification if files were uploaded and email is enabled
    if uploaded_count > 0 and EMAIL_ENABLED:
        send_upload_notification(uploaded_files, client_ip)
    
    # Send Signal notification if files were uploaded and Signal is enabled
    if uploaded_count > 0 and SIGNAL_ENABLED:
        send_upload_signal_notification(uploaded_files, client_ip)
    
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

