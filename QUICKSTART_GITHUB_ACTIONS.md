# Snabbstart: GitHub Actions för Stryktips Bot

Automatisk deployment till ditt k3s cluster med GitHub Actions i 5 minuter.

## 🚀 Snabbstart (5 minuter)

### Steg 1: Pusha till GitHub

```bash
cd /home/admbilly/stryktips-bot

# Lägg till alla nya filer
git add .github/ GITHUB_ACTIONS_SETUP.md QUICKSTART_GITHUB_ACTIONS.md

# Commit
git commit -m "Add GitHub Actions workflows for CI/CD"

# Push till GitHub (om du inte gjort det än)
# git remote add origin https://github.com/YOUR_USERNAME/stryktips-bot.git
git push origin main
```

### Steg 2: Sätt upp Self-Hosted Runner (2 minuter)

1. **Gå till ditt repo:** `https://github.com/YOUR_USERNAME/stryktips-bot`
2. **Settings** → **Actions** → **Runners** → **New self-hosted runner**
3. **Välj:** Linux + x64
4. **Kör kommandona som visas:**

```bash
# Snabbversion (kopiera din egen token från GitHub):
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Konfigurera (byt ut TOKEN och USERNAME):
./config.sh --url https://github.com/YOUR_USERNAME/stryktips-bot --token YOUR_GITHUB_TOKEN

# Installera som service
sudo ./svc.sh install
sudo ./svc.sh start
```

### Steg 3: Verifiera (30 sekunder)

Gå tillbaka till **Settings** → **Actions** → **Runners** i GitHub.
Du ska se din runner listad som **"Idle"** med grön prick ✅

### Steg 4: Testa! (1 minut)

**Alternativ A: Pusha kod för automatisk deploy**
```bash
# Gör en liten ändring
echo "# Test" >> README.md
git add README.md
git commit -m "Test automatic deployment"
git push origin main
```

**Alternativ B: Manuell deploy**
1. Gå till **Actions** tab i GitHub
2. Välj **"Manual Deploy"**
3. Klicka **"Run workflow"** → **"Run workflow"**

### Steg 5: Kolla resultat (1 minut)

1. **I GitHub:** Actions tab → Se workflow köra live
2. **Lokalt:** När klar, besök http://stryktips.local
3. **Terminal:** `sudo k3s kubectl get pods -n stryktips`

## ✅ Det är klart!

Nu kommer varje push till `main` branch automatiskt deploya till ditt k3s cluster.

## 📋 Vad händer nu?

### Automatiskt vid varje push till main:
1. ✅ Kör tester
2. ✅ Bygger Docker image
3. ✅ Pushar till lokal registry
4. ✅ Deplojar till k3s
5. ✅ Startar om pods
6. ✅ Verifierar deployment

### Du kan också:
- **Manuell deploy:** Actions → Manual Deploy → Run workflow
- **Se logs:** Actions → Välj workflow run → Kolla detaljer
- **Rollback:** Deploya en äldre commit manuellt

## 🐛 Problem?

### Runner inte synlig i GitHub
```bash
cd ~/actions-runner
sudo ./svc.sh status
sudo ./svc.sh start
```

### Docker permission denied
```bash
sudo usermod -aG docker $(whoami)
newgrp docker
cd ~/actions-runner && sudo ./svc.sh restart
```

### Workflow failed
1. Gå till Actions tab → Klicka på failed run
2. Kolla logs för varje steg
3. Kör lokalt: `./deploy-to-k3s.sh` för att se exakt fel

### k3s inte igång
```bash
sudo systemctl status k3s
sudo systemctl start k3s
```

## 📚 Nästa Steg

- **Läs full guide:** [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)
- **Lägg till tester:** Redigera `.github/workflows/ci.yml`
- **Lägg till notifications:** Se GITHUB_ACTIONS_SETUP.md för exempel

## 🎯 Workflows

**3 workflows skapade:**

1. **`deploy.yml`** - Auto-deploya vid push till main
2. **`ci.yml`** - Testa kod på pull requests
3. **`manual-deploy.yml`** - Manuell deploy med options

---

**Skapad:** 2025-10-27
**Funkar?** ⭐ Star repo om det hjälpte!
