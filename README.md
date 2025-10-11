# MYMSNGROUP File Upload Portal

A secure file upload portal with admin management.

## Quick Start

### Option 1: Docker Hub (Recommended) 🐳

```bash
# Pull and run from Docker Hub
docker run -d \
  --name fileuploadportal \
  -p 5000:5000 \
  -e ADMIN_PASSWORD="your-secure-password" \
  -v ./uploads:/app/uploads \
  --restart unless-stopped \
  williswschan/fileuploadportal:latest

# Access at: http://localhost:5000
```

### Option 2: Docker Compose

```bash
# Start the application
docker compose up -d

# Access at: http://localhost:5000
```

### Option 3: Python

**1. Install Dependencies**
```bash
pip3 install -r requirements.txt
```

**2. Set Admin Password (Recommended)**
```bash
export ADMIN_PASSWORD="your-secure-password"
```

**3. Run the Application**
```bash
python3 app.py
```

**4. Access the Portal**
- **URL:** http://localhost:5000
- **Admin Login:** http://localhost:5000/admin/login

## Admin Credentials
- **Password:** Set via `ADMIN_PASSWORD` environment variable
- **Default:** `admin123` (if environment variable not set)

⚠️ **IMPORTANT:** Set `ADMIN_PASSWORD` environment variable in production!

## Features
- Multi-file upload (up to 2GB per file)
- All file types accepted
- Admin panel (view, download, delete files)
- Brute force protection (5 attempts, 1-min lockout)
- Responsive design (mobile, tablet, desktop)

## Docker Deployment

### Start with Docker Compose
```bash
# Start in background
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Set Password with Docker
```bash
# Method 1: Environment variable
export ADMIN_PASSWORD="your-secure-password"
docker compose up -d

# Method 2: Direct in docker compose.yml
# Edit docker compose.yml and change:
# - ADMIN_PASSWORD=your-secure-password

# Method 3: Using .env file
echo "ADMIN_PASSWORD=your-secure-password" > .env
docker compose up -d
```

### Pull from Docker Hub
```bash
# Pull latest version
docker pull williswschan/fileuploadportal:latest

# Pull specific version
docker pull williswschan/fileuploadportal:v1.5

# Run container from Docker Hub
docker run -d \
  --name fileuploadportal \
  -p 5000:5000 \
  -e ADMIN_PASSWORD="your-password" \
  -v ./uploads:/app/uploads \
  --restart unless-stopped \
  williswschan/fileuploadportal:latest

# View logs
docker logs -f fileuploadportal

# Stop and remove
docker stop fileuploadportal
docker rm fileuploadportal
```

### Build Locally (For Development)
```bash
# Build image from source
docker build -t fileuploadportal .

# Or rebuild with Docker Compose
docker compose up -d --build
```

## Configuration

### Change Admin Password

**Method 1: Environment Variable (Recommended)**
```bash
# Temporary (current session only)
export ADMIN_PASSWORD="your-secure-password"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export ADMIN_PASSWORD="your-secure-password"' >> ~/.bashrc
source ~/.bashrc
```

**Method 2: Systemd Service**
```bash
# In your systemd service file
Environment="ADMIN_PASSWORD=your-secure-password"
```

**Method 3: Docker Environment**
```bash
# Set before starting
export ADMIN_PASSWORD="your-secure-password"
docker compose up -d

# Or edit docker compose.yml directly
```

### Change Max File Size
Edit `app.py` line 13:
```python
MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB
```

### Change Port
Edit `app.py` line 231:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

---
**MYMSNGROUP** © 2025

