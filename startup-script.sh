#!/usr/bin/env bash
set -e

LOG_FILE="/var/log/chatbot-startup.log"
exec > >(tee -a ${LOG_FILE}) 2>&1

echo "============================================================"
echo "[Chatbot Startup] Starting deployment at $(date)"
echo "============================================================"

# 1. Update OS packages
echo "[1/6] Updating system packages..."
apt-get update -y
apt-get install -y git python3 python3-pip python3-venv curl iptables

# 2. Setup project directory and clone repo
echo "[2/6] Setting up project directory..."
mkdir -p /opt/chatbot
if [ ! -d "/opt/chatbot/.git" ]; then
    echo "Cloning repository..."
    git clone https://github.com/yungoonkim/gcp-compute-engine-chatbot.git /opt/chatbot
else
    echo "Updating existing repository..."
    cd /opt/chatbot
    git pull origin main
fi

cd /opt/chatbot

# 3. Create Python Virtual Environment & install requirements
echo "[3/6] Setting up Python virtual environment..."
python3 -m venv /opt/chatbot/venv
/opt/chatbot/venv/bin/pip install --upgrade pip
/opt/chatbot/venv/bin/pip install -r requirements.txt

# 4. Retrieve GEMINI_API_KEY from Secret Manager
echo "[4/6] Retrieving GEMINI_API_KEY from Secret Manager..."
SECRET_KEY=""
for i in {1..5}; do
    SECRET_KEY=$(gcloud secrets versions access latest --secret=GEMINI_API_KEY --project=976675812314 2>/dev/null || true)
    if [ -n "$SECRET_KEY" ]; then
        echo "Successfully retrieved GEMINI_API_KEY from Secret Manager!"
        break
    fi
    echo "Waiting for gcloud/credentials ($i/5)..."
    sleep 3
done

cat << EOF > /opt/chatbot/.env
GEMINI_API_KEY=${SECRET_KEY}
GCP_SECRET_NAME=projects/976675812314/secrets/GEMINI_API_KEY
PORT=8000
EOF
chmod 600 /opt/chatbot/.env

# 5. Create and configure systemd service
echo "[5/6] Creating systemd service unit..."
cat << 'EOF' > /etc/systemd/system/chatbot.service
[Unit]
Description=Gemini Web Chatbot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chatbot
EnvironmentFile=/opt/chatbot/.env
ExecStart=/opt/chatbot/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable chatbot.service
systemctl restart chatbot.service

# 6. Forward port 80 to 8000 for standard web access
echo "[6/6] Configuring port forwarding (80 -> 8000)..."
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8000 || true

echo "============================================================"
echo "[Chatbot Startup] Deployment completed successfully at $(date)"
echo "Service status:"
systemctl status chatbot.service --no-pager || true
echo "============================================================"
