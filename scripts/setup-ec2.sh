#!/bin/bash
# ============================================================
# One-shot setup script for a fresh AWS EC2 t2.micro (Amazon Linux 2023)
# Run this ONCE after you SSH into your new instance:
#   bash setup-ec2.sh
# ============================================================
set -euo pipefail

echo "==> 1. System update"
sudo dnf update -y

echo "==> 2. Install Docker"
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
newgrp docker   # apply group without re-login

echo "==> 3. Install Docker Compose v2"
COMPOSE_VERSION="v2.27.1"
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL \
  "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
docker compose version

echo "==> 4. Add 2 GB swap (prevents OOM on 1 GB t2.micro)"
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h

echo "==> 5. Clone the project"
read -rp "Enter your GitHub repo URL (or press Enter to skip if you'll upload manually): " REPO_URL
if [[ -n "$REPO_URL" ]]; then
  git clone "$REPO_URL" app
  cd app
else
  echo "Skipping clone. Copy your project files to ~/app/ and cd into it."
  mkdir -p ~/app
  cd ~/app
fi

echo ""
echo "==> DONE. Next steps:"
echo "  1. Copy your backend/.env file to ~/app/backend/.env"
echo "     (use: scp -i your-key.pem backend/.env ec2-user@<IP>:~/app/backend/.env)"
echo "  2. cd ~/app"
echo "  3. docker compose -f docker-compose.yml -f docker-compose.aws.yml up -d --build"
echo "  4. Watch logs: docker compose logs -f"
