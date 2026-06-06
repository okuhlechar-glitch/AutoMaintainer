#!/bin/bash
# AutoMaintainer — Oracle Cloud ARM Instance Setup
# Run this on a fresh Ubuntu 22.04 ARM instance: bash oracle-setup.sh

set -e

echo "=== AutoMaintainer Backend Setup ==="

# 1. Install Docker
echo "[1/5] Installing Docker..."
apt-get update -qq
apt-get install -y -qq docker.io docker-compose-plugin git curl
systemctl enable docker
systemctl start docker

# 2. Open firewall (Oracle blocks ports by default via iptables)
echo "[2/5] Configuring firewall..."
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
iptables -I INPUT 7 -m state --state NEW -p tcp --dport 443 -j ACCEPT
apt-get install -y -qq iptables-persistent 2>/dev/null || true
netfilter-persistent save 2>/dev/null || true

# 3. Clone repo
echo "[3/5] Cloning repository..."
if [ ! -d "AutoMaintainer" ]; then
    git clone https://github.com/okuhlecharlieman/AutoMaintainer.git
fi
cd AutoMaintainer

# 4. Create .env if not exists
echo "[4/5] Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "!!! EDIT .env WITH YOUR KEYS !!!"
    echo "   nano .env"
    echo ""
    echo "   DASHSCOPE_API_KEY=your_dashscope_key"
    echo "   GITHUB_TOKEN=your_github_token"
    echo ""
    echo "Then run: docker compose -f docker-compose.backend.yml up -d --build"
else
    echo ".env already exists, starting backend..."
    docker compose -f docker-compose.backend.yml up -d --build
    echo ""
    echo "=== Backend is running ==="
    echo "Test it: curl http://localhost/api/health"
    echo "Your public IP: curl -s ifconfig.me"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. nano .env                          # add your API keys"
echo "  2. docker compose -f docker-compose.backend.yml up -d --build"
echo "  3. curl http://localhost/api/health   # verify it works"
echo "  4. Open http://<YOUR_ORACLE_IP>/docs  # test API in browser"
