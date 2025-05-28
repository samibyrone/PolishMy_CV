# Self-Hosting CVLatex Guide

## 🌐 Overview
This guide will help you self-host your CVLatex application on a VPS with a custom domain.

## 📋 Prerequisites
- A VPS (recommended: DigitalOcean, Linode, or Vultr)
- A domain name
- Basic command line knowledge

## 🖥️ VPS Setup (Ubuntu 22.04)

### 1. Initial Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y git nginx python3 python3-pip python3-venv ufw fail2ban

# Create application user
sudo adduser cvlatex
sudo usermod -aG sudo cvlatex
su - cvlatex
```

### 2. Install LaTeX (Full Installation)
```bash
# Install complete LaTeX distribution
sudo apt install -y texlive-full

# Verify installation
pdflatex --version
which pdflatex
```

### 3. Clone and Setup Application
```bash
# Clone your repository
git clone https://github.com/hyperpix/cvlatex.git
cd cvlatex

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install production server
pip install gunicorn

# Create directories
mkdir -p uploads output static
```

### 4. Environment Configuration
```bash
# Create environment file
cat > .env << EOF
FLASK_ENV=production
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
EOF

# Set permissions
chmod 600 .env
```

### 5. Test Application
```bash
# Test locally first
python app.py

# Test with Gunicorn
gunicorn --bind 0.0.0.0:8000 app:app
```

## 🌐 Domain and Nginx Setup

### 1. Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/cvlatex
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for LaTeX compilation
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Increase max body size for file uploads
        client_max_body_size 20M;
    }

    # Serve static files directly
    location /static {
        alias /home/cvlatex/cvlatex/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/cvlatex /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. SSL Certificate with Let's Encrypt
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

## 🔄 Process Management with Systemd

### 1. Create Systemd Service
```bash
sudo nano /etc/systemd/system/cvlatex.service
```

Add this configuration:
```ini
[Unit]
Description=CVLatex Flask Application
After=network.target

[Service]
User=cvlatex
Group=cvlatex
WorkingDirectory=/home/cvlatex/cvlatex
Environment=PATH=/home/cvlatex/cvlatex/venv/bin
EnvironmentFile=/home/cvlatex/cvlatex/.env
ExecStart=/home/cvlatex/cvlatex/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 --timeout 300 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable cvlatex
sudo systemctl start cvlatex
sudo systemctl status cvlatex
```

## 🔒 Security Setup

### 1. Configure Firewall
```bash
# Enable UFW
sudo ufw enable

# Allow essential services
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Check status
sudo ufw status
```

### 2. Fail2Ban Configuration
```bash
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true
```

Restart fail2ban:
```bash
sudo systemctl restart fail2ban
```

## 🔍 Monitoring and Logs

### 1. View Application Logs
```bash
# Application logs
sudo journalctl -u cvlatex -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. System Monitoring
```bash
# Install htop for system monitoring
sudo apt install htop

# Check disk usage
df -h

# Check memory usage
free -h
```

## 🔄 Deployment and Updates

### 1. Update Script
Create `/home/cvlatex/update.sh`:
```bash
#!/bin/bash
cd /home/cvlatex/cvlatex
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cvlatex
sudo systemctl reload nginx
echo "Deployment complete!"
```

Make executable:
```bash
chmod +x /home/cvlatex/update.sh
```

### 2. Automated Backups
Create `/home/cvlatex/backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/cvlatex/backups"
mkdir -p $BACKUP_DIR

# Backup uploads and output
tar -czf $BACKUP_DIR/cvlatex_data_$DATE.tar.gz uploads output

# Keep only last 7 backups
find $BACKUP_DIR -name "cvlatex_data_*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
crontab -e
# Add: 0 2 * * * /home/cvlatex/backup.sh
```

## 💰 Cost Breakdown

### VPS Options:
- **DigitalOcean Basic**: $6/month
- **Linode Nanode**: $5/month  
- **Vultr Regular**: $2.50/month
- **Hetzner CX11**: €4/month (~$4.30)

### Domain:
- **.com domain**: ~$10-15/year
- **SSL Certificate**: Free (Let's Encrypt)

### Total Monthly Cost: $3-8/month

## 🎯 Benefits of Self-Hosting

✅ **Full LaTeX Support** - Complete TeXLive installation
✅ **Custom Domain** - Professional appearance
✅ **Complete Control** - Install any packages you need
✅ **Better Performance** - Dedicated resources
✅ **Cost Effective** - Much cheaper than managed services
✅ **Learning Experience** - Gain valuable DevOps skills
✅ **Privacy** - Your data stays on your server

## 🔧 Alternative: Docker Deployment

If you prefer Docker, create a `Dockerfile`:
```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "300", "app:app"]
```

## 📞 Support and Troubleshooting

Common issues and solutions:
- **LaTeX compilation fails**: Check TeXLive installation
- **File upload issues**: Increase Nginx `client_max_body_size`
- **Timeout errors**: Increase proxy timeouts in Nginx
- **Permission errors**: Check file ownership and permissions

For help, check:
- Application logs: `sudo journalctl -u cvlatex`
- Nginx logs: `/var/log/nginx/`
- System resources: `htop`, `df -h` 