# MYMSNGROUP File Upload Portal

A secure file upload portal with admin management.

## Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Set Admin Password (Recommended)
```bash
# Set environment variable
export ADMIN_PASSWORD="your-secure-password"

# Or create .env file (copy from env.example)
cp env.example .env
# Then edit .env and change the password
```

### 3. Run the Application
```bash
python3 app.py
```

### 4. Access the Portal
- **URL:** http://localhost:5000
- **Admin Login:** http://localhost:5000/admin/login

## Admin Credentials
- **Password:** Set via `ADMIN_PASSWORD` environment variable
- **Default:** `admin123` (if environment variable not set)

⚠️ **IMPORTANT:** Set `ADMIN_PASSWORD` environment variable in production!

## Features
- Multi-file upload (up to 5GB per file)
- All file types accepted
- Admin panel (view, download, delete files)
- Brute force protection (5 attempts, 1-min lockout)
- Responsive design (mobile, tablet, desktop)

## Configuration

### Change Admin Password

**Method 1: Environment Variable (Recommended)**
```bash
# Linux/Mac - temporary (current session only)
export ADMIN_PASSWORD="your-secure-password"

# Linux/Mac - permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export ADMIN_PASSWORD="your-secure-password"' >> ~/.bashrc
source ~/.bashrc

# Or use .env file
cp env.example .env
# Edit .env and change ADMIN_PASSWORD value
```

**Method 2: Systemd Service**
```bash
# In your systemd service file
Environment="ADMIN_PASSWORD=your-secure-password"
```

**Method 3: Docker**
```bash
docker run -e ADMIN_PASSWORD="your-secure-password" ...
```

### Change Max File Size
Edit `app.py` line 13:
```python
MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5GB
```

### Change Port
Edit `app.py` line 231:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Firewall (Linux)
```bash
# Ubuntu/Debian
sudo ufw allow 5000/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## Production Deployment
Use Gunicorn:
```bash
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---
**MYMSNGROUP** © 2025

