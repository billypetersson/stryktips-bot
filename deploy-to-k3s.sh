#!/bin/bash
set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          STRYKTIPS BOT - K3S DEPLOYMENT SCRIPT              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Build Docker Image
echo -e "${BLUE}[1/7]${NC} Bygger Docker image..."
sudo docker build -t stryktips-bot:latest -t localhost:30500/stryktips-bot:latest .
echo -e "${GREEN}✓${NC} Docker image byggd\n"

# Step 2: Push to local registry
echo -e "${BLUE}[2/7]${NC} Pushar image till lokal registry..."
sudo docker push localhost:30500/stryktips-bot:latest || echo "⚠️  Varning: Kunde inte pusha till registry (kan ignoreras om registry inte körs)"
echo -e "${GREEN}✓${NC} Image pushad\n"

# Step 3: Create namespace
echo -e "${BLUE}[3/7]${NC} Skapar namespace..."
sudo k3s kubectl apply -f k8s/namespace.yaml
echo -e "${GREEN}✓${NC} Namespace skapad\n"

# Step 4: Apply secrets and configmap
echo -e "${BLUE}[4/7]${NC} Applicerar secrets och configmap..."
sudo k3s kubectl apply -f k8s/secrets.yaml
sudo k3s kubectl apply -f k8s/configmap.yaml
echo -e "${GREEN}✓${NC} Secrets och configmap applicerade\n"

# Step 5: Deploy application
echo -e "${BLUE}[5/7]${NC} Deplojar applikation..."
sudo k3s kubectl apply -f k8s/deployment.yaml
sudo k3s kubectl apply -f k8s/service.yaml
echo -e "${GREEN}✓${NC} Applikation deployad\n"

# Step 6: Setup ingress
echo -e "${BLUE}[6/7]${NC} Konfigurerar ingress..."
sudo k3s kubectl apply -f k8s/ingress.yaml
echo -e "${GREEN}✓${NC} Ingress konfigurerad\n"

# Step 7: Deploy cronjobs
echo -e "${BLUE}[7/7]${NC} Deplojar cronjobs..."
sudo k3s kubectl apply -f k8s/cronjob.yaml
sudo k3s kubectl apply -f k8s/cronjob-experts.yaml
echo -e "${GREEN}✓${NC} Cronjobs deployade\n"

# Wait for pods to be ready
echo -e "${YELLOW}Väntar på att pods ska bli redo...${NC}"
sudo k3s kubectl wait --for=condition=ready pod -l app=stryktips-bot -n stryktips --timeout=120s || true

# Show status
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT SLUTFÖRD                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${BLUE}Status:${NC}"
sudo k3s kubectl get pods -n stryktips
echo ""
sudo k3s kubectl get ingress -n stryktips
echo ""
sudo k3s kubectl get cronjobs -n stryktips

echo ""
echo -e "${GREEN}✓ Stryktips Bot är nu deployad i k3s!${NC}"
echo ""
echo "Åtkomst:"
echo "  • http://stryktips.local"
echo "  • Logs: sudo k3s kubectl logs -f -l app=stryktips-bot -n stryktips"
echo "  • Status: sudo k3s kubectl get all -n stryktips"
echo ""
