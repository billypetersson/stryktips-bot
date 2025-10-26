# Stryktips Bot ⚽

Automatisk analysbot för svenska Stryktips som hämtar odds, streckprocent och expertutlåtanden för att beräkna värde och generera optimala rader.

## Funktioner

- 📊 **Oddsjämförelse** - Hämtar odds från flera bookmakers (Bet365, Unibet, Betsson)
- 📈 **Värdeanalys** - Jämför odds med streckprocent för att identifiera värdetecken
- 👥 **Expertkonsensus** - Samlar och sammanfattar tips från svenska sportexperter
- 🎯 **Radgenerering** - Skapar optimala rader med max 2 helgarderingar
- 🔄 **Automatisk uppdatering** - K8s CronJob uppdaterar kupong varje fredag
- 🌐 **Webb-UI** - Snyggt gränssnitt med HTMX för interaktiv användning

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Frontend**: HTMX (server-renderad), vanilla CSS
- **Database**: PostgreSQL (med SQLite-stöd för lokal utveckling)
- **Deployment**: Docker, Kubernetes
- **Scheduling**: K8s CronJob (fredag 07:00 UTC = 08:00 Stockholm vintertid)

## Projektstruktur

```
stryktips-bot/
├── src/
│   ├── models/          # Database models
│   ├── database/        # Database session och init
│   ├── scrapers/        # Data scrapers (Svenska Spel, odds, experter)
│   ├── analysis/        # Värdeberäkning och radgenerering
│   ├── api/             # FastAPI routes
│   ├── templates/       # HTMX templates
│   ├── static/          # CSS och JavaScript
│   ├── jobs/            # Background jobs (CronJob)
│   └── main.py          # FastAPI app entrypoint
├── k8s/                 # Kubernetes manifests
├── scripts/             # Utility scripts
├── tests/               # Tester
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Installation & Setup

### Lokal Utveckling (Docker Compose)

1. **Klona projektet**
   ```bash
   git clone <repo-url>
   cd stryktips-bot
   ```

2. **Skapa .env fil**
   ```bash
   cp .env.example .env
   # Redigera .env om du vill ändra inställningar
   ```

3. **Bygg och starta med Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Initiera databasen** (första gången)
   ```bash
   docker-compose exec app python scripts/init_db.py
   ```

5. **Öppna webbläsare**
   ```
   http://localhost:8000
   ```

### Manuell Körning (Utan Docker)

1. **Installera Python 3.12+**

2. **Installera dependencies**
   ```bash
   pip install -r requirements.txt
   # Eller med Poetry:
   poetry install
   ```

3. **Skapa .env fil**
   ```bash
   cp .env.example .env
   ```

4. **Initiera databas**
   ```bash
   python scripts/init_db.py
   ```

5. **Kör applikationen**
   ```bash
   uvicorn src.main:app --reload
   ```

6. **Öppna webbläsare**
   ```
   http://localhost:8000
   ```

## Kubernetes Deployment

### Förutsättningar

- Kubernetes cluster (1.25+)
- kubectl installerat och konfigurerat
- Docker registry för att pusha image

### Deployment Steg

1. **Bygg och pusha Docker image**
   ```bash
   docker build -t <your-registry>/stryktips-bot:latest .
   docker push <your-registry>/stryktips-bot:latest
   ```

2. **Uppdatera image i deployment.yaml**
   ```bash
   # Ersätt "stryktips-bot:latest" med din image URL
   sed -i 's|image: stryktips-bot:latest|image: <your-registry>/stryktips-bot:latest|g' k8s/*.yaml
   ```

3. **Skapa secrets**
   ```bash
   cp k8s/secrets.example.yaml k8s/secrets.yaml
   # Redigera k8s/secrets.yaml och fyll i DATABASE_URL och andra hemligheter
   # OBS: Använd proper secrets management i produktion!
   ```

4. **Applicera Kubernetes manifests**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/secrets.yaml
   kubectl apply -f k8s/postgres.yaml      # Om du inte har extern DB
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   kubectl apply -f k8s/cronjob.yaml
   ```

5. **Verifiera deployment**
   ```bash
   kubectl get pods -n stryktips
   kubectl get services -n stryktips
   kubectl get cronjobs -n stryktips
   ```

6. **Initiera databas** (första gången)
   ```bash
   kubectl exec -n stryktips -it deployment/stryktips-app -- python scripts/init_db.py
   ```

7. **Testa manuell uppdatering**
   ```bash
   kubectl create job -n stryktips --from=cronjob/stryktips-updater manual-update-001
   kubectl logs -n stryktips job/manual-update-001
   ```

### CronJob Schema

CronJoben är konfigurerad att köra **varje fredag kl 07:00 UTC**:
- Vintertid (CET, UTC+1): 08:00 svensk tid
- Sommartid (CEST, UTC+2): 09:00 svensk tid

För att justera tiden, redigera `k8s/cronjob.yaml`:
```yaml
schedule: "0 7 * * 5"  # Fredag 07:00 UTC
```

**Tips**: Om din K8s cluster stödjer `timeZone` (v1.25+), kan du använda:
```yaml
timeZone: "Europe/Stockholm"
schedule: "0 8 * * 5"  # 08:00 Stockholm-tid året runt
```

## Användning

### Webb-UI

1. **Startsida** (`/`) - Visa senaste kupongen
2. **Kupongvy** (`/coupon/{id}`) - Lista alla matcher med streckprocent och rekommendationer
3. **Analys** (`/analysis/{id}`) - Detaljerad värdeanalys, odds och expertutlåtanden
4. **Uppdatera** - HTMX-knapp för manuell refresh

### API Endpoints

- `GET /` - Startsida
- `GET /coupon/{coupon_id}` - Specifik kupong
- `GET /analysis/{coupon_id}` - Detaljerad analys
- `POST /refresh` - Manuell uppdatering (HTMX)
- `GET /health` - Health check (för K8s probes)

### Manuell Uppdatering (CLI)

```bash
# Lokalt
python -m src.jobs.update_coupon

# Docker Compose
docker-compose exec app python -m src.jobs.update_coupon

# Kubernetes
kubectl create job -n stryktips --from=cronjob/stryktips-updater manual-update
```

## Konfiguration

Alla inställningar hanteras via miljövariabler (`.env` eller K8s ConfigMap/Secrets).

### Viktiga variabler

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/stryktips

# Application
LOG_LEVEL=INFO
DEBUG=false

# Scrapers
SCRAPE_TIMEOUT=30
SVENSKA_SPEL_BASE_URL=https://www.svenskaspel.se

# Analysis
MAX_HALF_COVERS=2           # Max antal helgarderingar per rad
MIN_VALUE_THRESHOLD=1.05     # Minsta värde för att rekommendera tecken

# Odds Providers (optional API keys)
BET365_API_KEY=
UNIBET_API_KEY=
BETSSON_API_KEY=
```

Se `.env.example` för fullständig lista.

## Development

### Code Style

Projektet använder:
- **Black** för formattering (line length: 100)
- **Ruff** för linting
- **mypy** för type checking

```bash
# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

### Tester

```bash
# Kör alla tester
pytest

# Med coverage
pytest --cov=src tests/

# Specifikt test
pytest tests/test_analysis.py
```

### Database Migrations (framtida)

Projektet är förberett för Alembic migrations:

```bash
# Skapa migration
alembic revision --autogenerate -m "description"

# Applicera migration
alembic upgrade head
```

## Dataflöde

1. **Fredag 07:00 UTC** - K8s CronJob triggas
2. **Scraping**:
   - Hämta kupong från Svenska Spel
   - Hämta odds från bookmakers
   - Hämta expertutlåtanden
3. **Analys**:
   - Beräkna implicerad sannolikhet från odds
   - Jämför med streckprocent för värde
   - Summera expertutlåtanden
4. **Radgenerering**:
   - Generera primär rad (högsta värde, inga helgarderingar)
   - Generera alternativa rader med strategiska helgarderingar
5. **Lagring** - Spara allt i PostgreSQL
6. **Webb-UI** - Visa resultat för användare

## Scrapers - VIKTIGT

**STATUS**: Svenska Spel API-integration är **implementerad** och redo att testas! 🎉

Se **[REAL_SCRAPING_STATUS.md](docs/REAL_SCRAPING_STATUS.md)** för fullständig status och instruktioner.

### Snabbsammanfattning:
- ✅ API endpoint identifierad och verifierad: `https://api.spela.svenskaspel.se/draw/1/stryktipset/draws`
- ✅ Scraper uppdaterad med flexibel parsing
- ✅ Fallback till Playwright (browser automation) om API inte fungerar
- ✅ Fallback till mock data för testning
- 🔧 Behöver testas när kupong öppnar (ikväll ca 20:00)

**Testa ikväll**:
```bash
# 1. Testa API-struktur
python scripts/test_api_structure.py

# 2. Kör full uppdatering med riktig data
rm -f stryktips.db
python scripts/init_db.py
python -m src.jobs.update_coupon

# 3. Öppna webb-UI och verifiera
# http://192.168.1.25:8000
```

---

För produktionsanvändning behöver du även implementera riktiga scrapers för:

### Svenska Spel
- Kupong och streckprocent
- Möjliga källor: officiell API, webscraping, RSS
- **Se till att följa deras användarvillkor**
- **📖 Se detaljerad guide**: [`docs/SCRAPING_GUIDE.md`](docs/SCRAPING_GUIDE.md)

**Implementationsalternativ:**

1. **Playwright/Selenium (Rekommenderat)**
   ```bash
   pip install playwright
   playwright install chromium
   ```
   Exempel-implementation finns i: `src/scrapers/svenska_spel_playwright.py`

2. **Reverse-engineera Svenska Spels API**
   - Öppna DevTools (F12) på https://spela.svenskaspel.se/stryktipset
   - Leta efter XHR-requests i Network-fliken
   - Kopiera endpoints och headers

3. **Använd odds-jämförelsesajter**
   - [The Odds API](https://the-odds-api.com/) - Kommersiell API-tjänst
   - Oddsportal, Flashscore (kräver scraping)

### Odds Providers
- Bet365, Unibet, Betsson, etc.
- Alternativ: [The Odds API](https://the-odds-api.com/), andra odds aggregators
- Många kräver API-nycklar

### Expert-utlåtanden
- Aftonbladet, Expressen, SVT Sport
- **Kontrollera robots.txt och användarvillkor**
- Överväg RSS-feeds eller officiella APIer

**Implementationsfiler att uppdatera**:
- `src/scrapers/svenska_spel.py` - Huvudimplementation
- `src/scrapers/svenska_spel_playwright.py` - Playwright-exempel
- `src/scrapers/odds_providers.py` - Odds-scrapers
- `src/scrapers/experts.py` - Expert-scrapers

## Rättsliga Överväganden

⚠️ **VIKTIGT**:
- Detta verktyg är för **personligt bruk och utbildningssyfte**
- Respektera användarvillkor för alla datakällor
- Scraping kan vara begränsat eller förbjudet - kolla alltid först
- Spela ansvarsfullt - detta är ingen garanti för vinst
- Svenska Spel och bookmakers förbjuder ofta automatiserad datainsamling

## Roadmap

- [ ] Implementera riktiga scrapers (ersätt mock data)
- [ ] Lägg till LLM-baserad sammanfattning av expertutlåtanden
- [ ] Förbättra värdeberäkning med historisk data
- [ ] Backtesting av radgenerering
- [ ] Webhook-notifieringar (Discord, Slack)
- [ ] Multi-rad optimering (reducerade system)
- [ ] Export till Excel/PDF

## Licens

MIT License - se LICENSE fil

## Disclaimer

**VIKTIGT**: Detta verktyg är för utbildningssyfte och personligt bruk. Det ger ingen garanti för vinst. Spela ansvarsfullt och satsa aldrig mer än du har råd att förlora.

**Svenska Spel** och alla bookmakers och mediekällor som nämns är registrerade varumärken som tillhör sina respektive ägare. Detta projekt är inte affilierat med eller endorsat av någon av dessa organisationer.

## Support & Bidrag

Om du hittar buggar eller har förbättringsförslag:
1. Skapa ett issue
2. Forka projektet och skapa en pull request

---

Byggt med ❤️ för svenska fotbollsentusiaster
# stryktips-bot
