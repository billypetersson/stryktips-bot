# GitHub Actions CI/CD Setup

Detta projekt använder GitHub Actions för att automatiskt bygga och deploya till ditt lokala k3s cluster.

## 📋 Översikt

**2 Workflows:**
1. **`ci.yml`** - Continuous Integration (körs på GitHub-hostade runners)
   - Testkörning
   - Linting och formatering
   - Docker image build test
   - Körs automatiskt på pull requests

2. **`deploy.yml`** - Deployment till k3s (körs på self-hosted runner)
   - Bygger Docker image
   - Pushar till lokal registry
   - Deplojar till k3s cluster
   - Körs automatiskt vid push till `main` branch
   - Kan också triggas manuellt

## 🏃 Sätta upp Self-Hosted Runner

Eftersom k3s clustret körs lokalt behöver du en self-hosted GitHub Actions runner på din maskin.

### Steg 1: Gå till Repository Settings

1. Gå till ditt GitHub repository: `https://github.com/YOUR_USERNAME/stryktips-bot`
2. Klicka på **Settings** → **Actions** → **Runners**
3. Klicka på **New self-hosted runner**
4. Välj **Linux** och **x64**

### Steg 2: Installera Runner på din maskin

GitHub visar kommandon att köra. Alternativt, använd dessa steg:

```bash
# Skapa katalog för runner
mkdir -p ~/actions-runner && cd ~/actions-runner

# Ladda ner senaste runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extrahera
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Konfigurera runner
./config.sh --url https://github.com/YOUR_USERNAME/stryktips-bot --token YOUR_TOKEN

# VIKTIGT: När den frågar om runner name, använd något unikt som "stryktips-local"
# När den frågar om labels, lägg till: self-hosted,Linux,X64,k3s
```

### Steg 3: Installera Runner som systemd Service

För att runnern ska köra automatiskt vid systemstart:

```bash
cd ~/actions-runner
sudo ./svc.sh install
sudo ./svc.sh start
```

**Kontrollera status:**
```bash
sudo ./svc.sh status
```

### Steg 4: Ge Runner Docker-rättigheter

Runnern behöver kunna köra Docker-kommandon:

```bash
# Lägg till runner-användaren i docker-gruppen
sudo usermod -aG docker $(whoami)

# Om runnern körs som annan användare (t.ex. 'runner'):
# sudo usermod -aG docker runner

# Logga ut och in igen för att ändringarna ska gälla
# Eller starta om runner-servicen:
sudo ./svc.sh stop
sudo ./svc.sh start
```

### Steg 5: Verifiera Installation

1. Gå tillbaka till **Settings** → **Actions** → **Runners** i GitHub
2. Du borde se din runner listad som **"Idle"** (grön)

## 🚀 Använda Workflows

### Automatisk Deployment

När du pushar till `main` branch:

```bash
git add .
git commit -m "Deploy new changes"
git push origin main
```

GitHub Actions kommer automatiskt:
1. Bygga Docker image
2. Deploya till k3s cluster
3. Starta om pods med nya imagen
4. Verifiera att deployment fungerar

### Manuell Deployment

1. Gå till **Actions** tab i GitHub
2. Välj **"Deploy to K3s"** workflow
3. Klicka **"Run workflow"**
4. Välj branch och klicka **"Run workflow"**

### Visa Workflow Logs

1. Gå till **Actions** tab
2. Klicka på en workflow run
3. Klicka på job name för att se detaljerade logs

## 🔒 Secrets & Environment Variables

Om du behöver lägga till hemligheter (API keys, etc.):

1. Gå till **Settings** → **Secrets and variables** → **Actions**
2. Klicka **"New repository secret"**
3. Lägg till dina secrets (t.ex. `SVENSKA_SPEL_API_KEY`)

Använd sedan i workflow:
```yaml
- name: Use secret
  env:
    API_KEY: ${{ secrets.SVENSKA_SPEL_API_KEY }}
  run: |
    echo "Using API key..."
```

## 🐛 Felsökning

### Runner är Offline

Kör på din lokala maskin:
```bash
cd ~/actions-runner
sudo ./svc.sh status
sudo ./svc.sh start
```

### Docker Permission Denied

```bash
# Kontrollera docker group membership
groups

# Om 'docker' inte finns i listan:
sudo usermod -aG docker $(whoami)
newgrp docker
sudo ./svc.sh restart
```

### Workflow Failed

1. Gå till **Actions** tab och klicka på failed run
2. Kolla logs för varje steg
3. Vanliga problem:
   - k3s inte igång: `sudo systemctl status k3s`
   - Docker daemon inte igång: `sudo systemctl status docker`
   - Registry inte tillgänglig: kolla `localhost:30500`

### k3s Deployment Issues

```bash
# Kolla pod status
sudo k3s kubectl get pods -n stryktips

# Visa pod logs
sudo k3s kubectl logs -f -l app=stryktips-bot -n stryktips

# Beskriv pod för att se fel
sudo k3s kubectl describe pod <pod-name> -n stryktips

# Starta om deployment manuellt
sudo k3s kubectl rollout restart deployment/stryktips-deployment -n stryktips
```

## 📊 Workflow Status Badges

Lägg till i din README.md:

```markdown
![Deploy Status](https://github.com/YOUR_USERNAME/stryktips-bot/workflows/Deploy%20to%20K3s/badge.svg)
![CI Status](https://github.com/YOUR_USERNAME/stryktips-bot/workflows/CI%20-%20Test%20%26%20Build/badge.svg)
```

## ⚙️ Avancerad Konfiguration

### Notification vid Deployment

För att få notifikationer (t.ex. Slack, Discord, email) vid deployment:

1. Lägg till secret för webhook URL
2. Lägg till notification step i `deploy.yml`:

```yaml
- name: Send notification
  if: always()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"Deployment ${{ job.status }}: http://stryktips.local"}'
```

### Conditional Deployment

För att deploya bara om vissa filer ändrats:

```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - 'k8s/**'
      - 'Dockerfile'
```

### Multiple Environments

För att stödja staging/production:

```yaml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    # ... deploy to staging

  deploy-production:
    if: github.ref == 'refs/heads/main'
    # ... deploy to production
```

## 📚 Nästa Steg

1. ✅ Sätt upp self-hosted runner
2. ✅ Testa workflow genom att pusha kod
3. ⏳ Lägg till riktiga tester i CI workflow
4. ⏳ Lägg till deployment notifications
5. ⏳ Överväg staging environment

## 🤝 Support

Vid problem:
1. Kolla workflow logs i GitHub Actions tab
2. Kolla runner logs: `sudo journalctl -u actions.runner.*`
3. Kolla k3s logs: `sudo k3s kubectl logs -f -l app=stryktips-bot -n stryktips`

---

**Skapad:** 2025-10-27
**Senast uppdaterad:** 2025-10-27
