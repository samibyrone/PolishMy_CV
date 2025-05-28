# 🏠 Local Hosting Guide for CVLatex with Custom Domain

## ✅ **Why Local Hosting is Perfect for You**

Your local setup is already **PERFECT** for CVLatex:
- ✅ **LaTeX Working**: MiKTeX-pdfTeX 4.18 (MiKTeX 24.1) fully functional
- ✅ **Python Environment**: Python 3.11.9 with all dependencies
- ✅ **Fast Performance**: No cloud limitations or timeouts
- ✅ **Full Control**: Complete control over your application

## 🌍 **Custom Domain Options**

### **Option 1: Free Dynamic DNS (Easiest)**

#### **Using No-IP (Free)**
1. **Sign up at [No-IP.com](https://www.noip.com/)**
   - Get a free subdomain like `yourname.ddns.net`
   - Free plan includes 3 hostnames

2. **Install No-IP DUC (Dynamic Update Client)**
   ```bash
   # Download from: https://www.noip.com/download
   # Automatically updates your IP when it changes
   ```

3. **Configure Port Forwarding**
   ```
   Router Settings:
   - External Port: 80 (or 8000)
   - Internal Port: 5000 (or your app port)
   - Internal IP: Your PC's local IP (e.g., 192.168.1.100)
   ```

#### **Using Duck DNS (Free)**
1. **Go to [DuckDNS.org](https://www.duckdns.org/)**
2. **Get subdomain**: `yourname.duckdns.org`
3. **Set up auto-update script**

### **Option 2: Paid Custom Domain ($10-15/year)**

#### **Buy Domain + DNS Service**
1. **Purchase domain** from:
   - Namecheap ($8-12/year)
   - GoDaddy ($10-15/year)
   - Cloudflare ($8-10/year)

2. **Set up Dynamic DNS**:
   - Use Cloudflare API for automatic IP updates
   - Point A record to your home IP

## 🚀 **Setup Methods**

### **Method 1: Simple Development Server**

**For personal/testing use:**
```bash
cd D:\CVLatex
python app.py
```
- Runs on: `http://localhost:5000`
- Access via domain: Set up port forwarding

### **Method 2: Production-Ready with Gunicorn**

**For better performance and stability:**

1. **Create production script** (`start_server.bat`):
```batch
@echo off
echo Starting CVLatex Production Server...
cd /d "D:\CVLatex"
gunicorn app:app --bind 0.0.0.0:8000 --workers 2 --timeout 120 --access-logfile access.log --error-logfile error.log
pause
```

2. **Run the server**:
```bash
gunicorn app:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

### **Method 3: Windows Service (Advanced)**

**Run as background service:**

1. **Install NSSM** (Non-Sucking Service Manager):
   ```bash
   # Download from: https://nssm.cc/download
   ```

2. **Create service**:
   ```bash
   nssm install CVLatex
   # Set Application path to: python.exe
   # Set Arguments: D:\CVLatex\app.py
   # Set Startup directory: D:\CVLatex
   ```

## 🔒 **Security & SSL Setup**

### **Option 1: Cloudflare Tunnel (Recommended)**

**Free SSL + Security:**
1. **Install Cloudflared**:
   ```bash
   # Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
   ```

2. **Create tunnel**:
   ```bash
   cloudflared tunnel create cvlatex
   cloudflared tunnel route dns cvlatex yourdomain.com
   cloudflared tunnel run cvlatex
   ```

3. **Benefits**:
   - ✅ Free SSL certificate
   - ✅ DDoS protection
   - ✅ No port forwarding needed
   - ✅ Hide your home IP

### **Option 2: Let's Encrypt + Nginx**

**Traditional SSL setup:**

1. **Install Nginx** on Windows
2. **Configure reverse proxy**:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Get SSL certificate**:
   ```bash
   # Use Certbot for Windows
   # Or use Cloudflare for free SSL
   ```

## 🛠️ **Complete Setup Example**

### **1. Production Flask Configuration**

Create `production_config.py`:
```python
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = False
    TESTING = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'output'
    
    # Security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
```

### **2. Production Startup Script**

Create `start_production.py`:
```python
import os
from app import app
from production_config import ProductionConfig

if __name__ == '__main__':
    app.config.from_object(ProductionConfig)
    
    # Create directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    print("🚀 Starting CVLatex Production Server...")
    print(f"📍 LaTeX Status: {'✅ Available' if app.config.get('LATEX_AVAILABLE') else '❌ Not Available'}")
    
    # Run with production settings
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8000)),
        debug=False,
        threaded=True
    )
```

### **3. Monitoring & Logs**

Create `monitor.py`:
```python
import psutil
import time
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='cvlatex_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def monitor_system():
    while True:
        # CPU and Memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('D:')
        
        # Log system stats
        logging.info(f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
        
        # Check if app is running
        # Add process monitoring logic here
        
        time.sleep(300)  # Check every 5 minutes

if __name__ == '__main__':
    monitor_system()
```

## 📊 **Recommended Complete Setup**

### **Best Practice Configuration:**

1. **Domain**: Buy from Namecheap ($10/year)
2. **DNS**: Use Cloudflare (Free)
3. **SSL**: Cloudflare Tunnel (Free + Secure)
4. **Server**: Gunicorn production server
5. **Monitoring**: Custom monitoring script
6. **Backup**: Automatic file backups

### **Total Cost**: ~$10/year for domain only!

## 🎯 **Quick Start Commands**

```bash
# 1. Start production server
cd D:\CVLatex
gunicorn app:app --bind 0.0.0.0:8000 --workers 2

# 2. Set up Cloudflare tunnel (one-time)
cloudflared tunnel create cvlatex
cloudflared tunnel route dns cvlatex yourdomain.com

# 3. Run tunnel (keep running)
cloudflared tunnel run cvlatex
```

## 🔧 **Maintenance & Updates**

### **Regular Tasks:**
- **Backup files**: Weekly backup of uploads/output folders
- **Update dependencies**: Monthly `pip install -r requirements.txt --upgrade`
- **Monitor logs**: Check access.log and error.log
- **SSL renewal**: Automatic with Cloudflare

### **Performance Optimization:**
- **File cleanup**: Auto-delete old uploads/outputs
- **Log rotation**: Prevent log files from growing too large
- **Resource monitoring**: Track CPU/memory usage

## 🎉 **Benefits of Local Hosting**

✅ **Perfect LaTeX**: Your MiKTeX works flawlessly  
✅ **No Timeouts**: No cloud platform limitations  
✅ **Full Control**: Complete control over environment  
✅ **Cost Effective**: Only ~$10/year for domain  
✅ **Fast Performance**: Local processing speed  
✅ **Privacy**: Your data stays on your machine  
✅ **Custom Features**: Add any features you want  

## 🚨 **Important Notes**

- **Firewall**: Configure Windows Firewall to allow your app
- **Antivirus**: Whitelist your app folder if needed
- **Power Management**: Disable sleep mode for 24/7 operation
- **Internet**: Ensure stable internet connection
- **Backup**: Regular backups of your application and data

Your local setup is already **perfect** for CVLatex! 🎉 