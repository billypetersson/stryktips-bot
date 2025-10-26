# Stryktips Bot ⚽

Automatisk analysbot för svenska Stryktips som hämtar odds, streckprocent och expertutlåtanden för att beräkna värde och generera optimala rader.

## Funktioner

- 📊 **Oddsjämförelse** - Hämtar odds från flera bookmakers (Bet365, Unibet, Betsson)
- 📈 **Värdeanalys** - Jämför odds med streckprocent för att identifiera värdetecken
- 👥 **Expertkonsensus** - Samlar och sammanfattar tips från svenska sportexperter
- 🎯 **Radgenerering** - Skapar optimala rader med max 2 helgarderingar
- 🔄 **Automatisk uppdatering** - K8s CronJob uppdaterar kupong och experttips dagligen
- 🌐 **Webb-UI** - Snyggt gränssnitt med HTMX för interaktiv användning
- 📰 **Expert-ingest** - Automatisk hämtning från 6+ svenska källor (Rekatochklart, Aftonbladet, Expressen, m.fl.)
- ⚽ **Fotbollshistorik** - Databas med engelsk fotbollsdata från Football-Data.co.uk och footballcsv

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0
- **Frontend**: HTMX (server-renderad), vanilla CSS
- **Database**: PostgreSQL (med SQLite-stöd för lokal utveckling)
- **Scraping**: httpx, BeautifulSoup4, Playwright (optional)
- **Deployment**: Docker, Kubernetes (k3s)
- **Scheduling**: K8s CronJob
- **Migrations**: Alembic

## Projektstruktur

```
stryktips-bot/
├── src/
│   ├── models/              # Database models
│   │   ├── coupon.py        # Stryktips kupong
│   │   ├── match.py         # Matcher
│   │   ├── odds.py          # Odds från bookmakers
│   │   ├── expert_item.py   # Expert predictions (NYT!)
│   │   ├── analysis.py      # Värdeanalys
│   │   └── football/        # Fotbollshistorik (NYT!)
│   ├── database/            # Database session och init
│   ├── scrapers/            # Data scrapers (Svenska Spel, odds)
│   ├── providers/           # Data providers (NYT!)
│   │   ├── experts/         # Expert prediction providers
│   │   │   ├── base.py      # Base provider med rate limiting
│   │   │   ├── rekatochklart.py
│   │   │   ├── aftonbladet.py
│   │   │   ├── stryktipspodden.py
│   │   │   └── generic_blog.py
│   │   ├── football_data_uk.py
│   │   └── footballcsv.py
│   ├── services/            # Business logic services (NYT!)
│   │   ├── expert_consensus.py
│   │   └── football_history.py
│   ├── analysis/            # Värdeberäkning och radgenerering
│   ├── api/                 # FastAPI routes
│   ├── templates/           # Jinja2 templates
│   │   ├── index.html       # Startsida
│   │   ├── analysis.html    # Analys med expert consensus
│   │   └── experts.html     # Experttips-sida (NYT!)
│   ├── static/              # CSS och JavaScript
│   ├── jobs/                # Background jobs (CronJob)
│   │   ├── update_coupon.py
│   │   └── fetch_expert_predictions.py  # (NYT!)
│   └── main.py              # FastAPI app entrypoint
├── k8s/                     # Kubernetes manifests
│   ├── deployment.yaml
│   ├── cronjob.yaml         # Kupong-uppdatering
│   ├── cronjob-experts.yaml # Expert-hämtning (NYT!)
│   └── ...
├── alembic/                 # Database migrations
│   └── versions/
├── scripts/                 # Utility scripts
├── tests/                   # Tester
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

4. **Kör migrations** (första gången)
   ```bash
   docker-compose exec app alembic upgrade head
   ```

5. **Öppna webbläsare**
   ```
   http://localhost:8000
   ```

### Manuell Körning (Utan Docker)

1. **Installera Python 3.12+**

2. **Installera dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Skapa .env fil**
   ```bash
   cp .env.example .env
   ```

4. **Kör migrations**
   ```bash
   alembic upgrade head
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
   # Ersätt "localhost:30500/stryktips-bot:latest" med din image URL
   sed -i 's|image: localhost:30500/stryktips-bot:latest|image: <your-registry>/stryktips-bot:latest|g' k8s/*.yaml
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
   kubectl apply -f k8s/ingress.yaml       # (optional)
   kubectl apply -f k8s/cronjob.yaml       # Kupong-uppdatering
   kubectl apply -f k8s/cronjob-experts.yaml  # Expert-hämtning (NYT!)
   ```

5. **Verifiera deployment**
   ```bash
   kubectl get pods -n stryktips
   kubectl get services -n stryktips
   kubectl get cronjobs -n stryktips
   ```

6. **Kör migrations** (första gången)
   ```bash
   kubectl exec -n stryktips -it deployment/stryktips-app -- alembic upgrade head
   ```

7. **Testa manuell uppdatering**
   ```bash
   # Kupong-uppdatering
   kubectl create job -n stryktips --from=cronjob/stryktips-updater manual-update-$(date +%s)

   # Expert-hämtning
   kubectl create job -n stryktips --from=cronjob/stryktips-experts-fetcher manual-experts-$(date +%s)

   # Se logs
   kubectl logs -n stryktips -l component=cronjob --tail=100
   ```

### CronJob Schema

**Kupong-uppdatering** (`cronjob.yaml`):
- Schema: Varje söndag kl 20:00 Stockholm-tid
- Timezone: Europe/Stockholm
- Hämtar kupong, odds, kör analys och radgenerering

**Expert-hämtning** (`cronjob-experts.yaml`):
- Schema: Dagligen kl 08:00 Stockholm-tid
- Timezone: Europe/Stockholm
- Hämtar experttips från alla källor
- Cleanup av gamla predictions (>30 dagar)

## Användning

### Webb-UI

1. **Startsida** (`/`) - Visa senaste kupongen med rekommendationer
2. **Kupongvy** (`/coupon/{id}`) - Lista alla matcher med streckprocent
3. **Analys** (`/analysis/{id}`) - Detaljerad värdeanalys med **expert consensus** ⭐
4. **Experttips** (`/experts`) - Visa alla experttips från svenska källor ⭐ NYT!
5. **Uppdatera** - HTMX-knapp för manuell refresh

### API Endpoints

#### Kupong & Analys
- `GET /` - Startsida
- `GET /coupon/{coupon_id}` - Specifik kupong
- `GET /analysis/{coupon_id}` - Detaljerad analys med expert consensus
- `POST /refresh` - Manuell uppdatering (HTMX)
- `GET /health` - Health check (för K8s probes)

#### Expert Predictions (NYT!) ⭐
- `GET /api/experts/latest?limit=50&source=Rekatochklart` - Senaste experttips
- `GET /api/experts/consensus/{match_id}` - Consensus för specifik match
- `GET /api/experts/consensus/coupon/{coupon_id}` - Consensus för hela kupongen
- `GET /experts` - HTML-sida med alla experttips

### Manuell Körning av Jobs

```bash
# Kupong-uppdatering
python -m src.jobs.update_coupon

# Expert-hämtning (NYT!)
python -m src.jobs.fetch_expert_predictions

# Docker Compose
docker-compose exec app python -m src.jobs.fetch_expert_predictions

# Kubernetes
kubectl create job -n stryktips --from=cronjob/stryktips-experts-fetcher manual-experts
```

### Ladda Fotbollshistorik (NYT!)

```bash
# Ladda Premier League-data från Football-Data.co.uk
python scripts/load_football_history.py

# Ladda från footballcsv (GitHub)
python scripts/load_football_history.py --provider footballcsv --competition eng.1
```

## Expert-Ingest System ⭐ NYT!

### Supported Källor

Systemet hämtar automatiskt experttips från följande svenska källor:

1. **Rekatochklart** - Populär Stryktipsblogg
2. **Aftonbladet Sportbladet** - Dagstidning (respekterar paywall)
3. **Expressen Tips & Odds** - Dagstidning
4. **Stryktipspodden** - Podcast med RSS-feed support
5. **Tipsmedoss** - Spelblogg
6. **Spelbloggare** - Plattform med flera bloggare

### Features

- ✅ **Rate limiting** - Polite scraping med konfigurerbar delay
- ✅ **Retry logic** - Exponential backoff vid fel
- ✅ **Team name matching** - Fuzzy matching mot databas
- ✅ **Swedish date parsing** - Stöd för svenska månadsnamn och relativa datum
- ✅ **Source attribution** - Alla tips länkas till original-artikel
- ✅ **Consensus calculation** - Beräknar majoritetsopinion per match
- ✅ **Weighted consensus** - Viktar källor baserat på tillförlitlighet

### Arkitektur

```python
# Base provider med rate limiting
class BaseExpertProvider:
    async def fetch_latest_predictions(self, max_items: int) -> list[ExpertPrediction]
    async def _fetch_html(self, url: str) -> str
    def _parse_swedish_date(self, date_str: str) -> datetime
    def _parse_pick(self, raw_pick: str) -> str

# Expert consensus service
class ExpertConsensusService:
    async def fetch_and_save_latest_predictions() -> dict[str, int]
    async def get_consensus_for_match(match_id: int) -> dict
    async def get_consensus_for_coupon(coupon_id: int) -> list[dict]
```

### Database Schema

**expert_items** tabell:
- `id` - Primary key
- `source` - Källans namn (Rekatochklart, Aftonbladet, etc.)
- `author` - Expert/skribent (optional)
- `published_at` - Publiceringsdatum
- `url` - Länk till original-artikel
- `match_id` - Foreign key till matches (nullable för generella artiklar)
- `pick` - Tips ('1', 'X', '2', '1X', '12', 'X2')
- `rationale` - Motivering (optional)
- `confidence` - Säkerhetsgrad (optional)
- `scraped_at` - När tipset hämtades
- `raw_data` - Rådata för debugging

**Indexes:**
- `ix_expert_items_source` - För filtrering per källa
- `ix_expert_items_published_at` - För tidsbaserad hämtning
- `ix_expert_items_match_id` - För match-specifika queries
- `ix_expert_items_source_published` - Kombinerat index
- `ix_expert_items_match_source` - För consensus-beräkning

## Fotbollshistorik-modul ⭐ NYT!

Fullständig databas för engelsk fotbollshistorik med normaliserat schema.

### Database Schema

7 tabeller för fotbollsdata:
- **competitions** - Ligor (Premier League, Championship, etc.)
- **seasons** - Säsonger (2023-24, 2024-25, etc.)
- **teams** - Lag med normaliserade namn
- **venues** - Arenor
- **matches** - Matcher med resultat
- **events** - Händelser (mål, kort, byten)
- **standings** - Tabellställning

### Data Providers

1. **Football-Data.co.uk** - Gratis CSV-data för engelska ligor
2. **footballcsv (GitHub)** - Open source CC0-licens
3. *Fler kan läggas till (Wikipedia, FiveThirtyEight, etc.)*

### Användning

```python
from src.services.football_history import FootballHistoryService
from src.providers.football_data_uk import FootballDataUKProvider

async with async_session_maker() as db:
    # Ladda data från provider
    provider = FootballDataUKProvider()
    matches = await provider.fetch_season_matches("E0", "2023-24")

    # Spara till databas
    service = FootballHistoryService(db)
    stats = await service.load_matches(matches)
    print(f"Loaded {stats['matches']} matches")
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

# Expert Providers (NYT!)
ENABLE_REKATOCHKLART=true
ENABLE_AFTONBLADET=true
ENABLE_STRYKTIPSPODDEN=true
ENABLE_EXPRESSEN=true
ENABLE_TIPSMEDOSS=true
ENABLE_SPELBLOGGARE=true

# Football History Providers (NYT!)
ENABLE_FOOTBALL_DATA_UK=true
ENABLE_FOOTBALLCSV=true
ENABLE_FIVETHIRTYEIGHT=false
ENABLE_WIKIPEDIA=false

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
pytest tests/test_expert_consensus.py
```

### Database Migrations

Projektet använder Alembic för migrations:

```bash
# Skapa migration
alembic revision --autogenerate -m "description"

# Applicera migration
alembic upgrade head

# Rollback
alembic downgrade -1

# Se status
alembic current
alembic history
```

**OBS**: För SQLite/PostgreSQL-kompatibilitet, använd manuella migrations för JSONB-fält:
```python
# I migration-filen
from alembic import context

json_type = sa.JSON() if 'sqlite' in str(context.get_bind().engine.url) else postgresql.JSONB(astext_type=Text())
```

## Dataflöde

### Huvuduppdatering (Söndag 20:00)
1. **K8s CronJob triggas** (`stryktips-updater`)
2. **Scraping**:
   - Hämta kupong från Svenska Spel
   - Hämta odds från bookmakers
   - Hämta expertutlåtanden (gamla systemet)
3. **Analys**:
   - Beräkna implicerad sannolikhet från odds
   - Jämför med streckprocent för värde
   - Summera expertutlåtanden
4. **Radgenerering**:
   - Generera primär rad (högsta värde, inga helgarderingar)
   - Generera alternativa rader med strategiska helgarderingar
5. **Lagring** - Spara allt i PostgreSQL
6. **Webb-UI** - Visa resultat för användare

### Expert-uppdatering (Dagligen 08:00) ⭐ NYT!
1. **K8s CronJob triggas** (`stryktips-experts-fetcher`)
2. **Fetch från alla källor**:
   - Rekatochklart - RSS/HTML scraping
   - Aftonbladet - HTML scraping (respekterar paywall)
   - Expressen - HTML scraping
   - Stryktipspodden - RSS feed + show notes
   - Tipsmedoss - HTML scraping
   - Spelbloggare - HTML scraping
3. **Processing**:
   - Normalisera lagnamn för matching
   - Parsa svenska datum ("26 oktober 2025", "Igår", etc.)
   - Parsa pick-tecken (1, X, 2, 1X, etc.)
   - Matcha mot matcher i databasen (fuzzy matching)
4. **Lagring**:
   - Spara till `expert_items` tabell
   - Hoppa över dubletter (samma URL + match)
5. **Consensus-beräkning**:
   - Räknas on-demand när användare öppnar analys-sidan
   - Viktad efter källans tillförlitlighet
   - Grupperas per match och källa

## Scrapers - VIKTIGT

**STATUS**: Svenska Spel API-integration är **implementerad** och redo att testas! 🎉

Se **[REAL_SCRAPING_STATUS.md](docs/REAL_SCRAPING_STATUS.md)** för fullständig status och instruktioner.

### Snabbsammanfattning:
- ✅ API endpoint identifierad och verifierad: `https://api.spela.svenskaspel.se/draw/1/stryktipset/draws`
- ✅ Scraper uppdaterad med flexibel parsing
- ✅ Fallback till Playwright (browser automation) om API inte fungerar
- ✅ Fallback till mock data för testning
- ✅ Expert-scrapers för 6+ svenska källor implementerade (NYT!)
- ✅ Fotbollshistorik från Football-Data.co.uk och footballcsv (NYT!)
- 🔧 Svenska Spel behöver testas när kupong öppnar

**Testa ikväll**:
```bash
# 1. Testa API-struktur
python scripts/test_api_structure.py

# 2. Kör full uppdatering med riktig data
rm -f stryktips.db
alembic upgrade head
python -m src.jobs.update_coupon

# 3. Hämta experttips
python -m src.jobs.fetch_expert_predictions

# 4. Öppna webb-UI och verifiera
# http://localhost:8000
# http://localhost:8000/experts
# http://localhost:8000/analysis/2
```

---

För produktionsanvändning behöver du även implementera riktiga scrapers för:

### Odds Providers
- Bet365, Unibet, Betsson, etc.
- Alternativ: [The Odds API](https://the-odds-api.com/), andra odds aggregators
- Många kräver API-nycklar

**Implementationsfiler att uppdatera**:
- `src/scrapers/svenska_spel.py` - Huvudimplementation
- `src/scrapers/svenska_spel_playwright.py` - Playwright-exempel
- `src/scrapers/odds_providers.py` - Odds-scrapers

## Rättsliga Överväganden

⚠️ **VIKTIGT**:
- Detta verktyg är för **personligt bruk och utbildningssyfte**
- Respektera användarvillkor för alla datakällor
- Scraping kan vara begränsat eller förbjudet - kolla alltid `robots.txt` först
- Spela ansvarsfullt - detta är ingen garanti för vinst
- Svenska Spel och bookmakers förbjuder ofta automatiserad datainsamling
- **Expert-providers**: All data attributeras till ursprungskällan med länkar

### Rate Limiting & Etik
- Alla expert-providers använder rate limiting (2-3 sekunder mellan requests)
- Retry-logik med exponential backoff
- Respekterar paywalls (Aftonbladet)
- User-Agent identifierar boten: `StryktipsBot/1.0`

## Roadmap

### Färdigt ✅
- [x] Implementera Svenska Spel API-scraper
- [x] Expert-ingest system med 6+ källor
- [x] Expert consensus calculation
- [x] Fotbollshistorik-modul
- [x] Database migrations med Alembic
- [x] Svensk datumparsing
- [x] K8s CronJobs för automatisering

### Planerat 🚧
- [ ] LLM-baserad sammanfattning av expertutlåtanden (GPT-4/Claude)
- [ ] Förbättra värdeberäkning med historisk data (machine learning)
- [ ] Backtesting av radgenerering mot historiska resultat
- [ ] Webhook-notifieringar (Discord, Slack, Telegram)
- [ ] Multi-rad optimering (reducerade system)
- [ ] Export till Excel/PDF
- [ ] Email-notifieringar när nya experttips finns
- [ ] Sentiment-analys av expert-rationale
- [ ] Ytterligare expert-källor (podcasts med ASR-transcription)
- [ ] Mobile-optimerad UI

## Licens

MIT License - se LICENSE fil

## Disclaimer

**VIKTIGT**: Detta verktyg är för utbildningssyfte och personligt bruk. Det ger ingen garanti för vinst. Spela ansvarsfullt och satsa aldrig mer än du har råd att förlora.

**Svenska Spel** och alla bookmakers och mediekällor som nämns (Rekatochklart, Aftonbladet, Expressen, Stryktipspodden, Tipsmedoss, Spelbloggare, Football-Data.co.uk, footballcsv) är registrerade varumärken eller öppen källkod som tillhör sina respektive ägare. Detta projekt är inte affilierat med eller endorsat av någon av dessa organisationer.

All data från expert-källor attributeras korrekt med källhänvisning och länkar till original-artiklar.

## Support & Bidrag

Om du hittar buggar eller har förbättringsförslag:
1. Skapa ett issue på GitHub
2. Forka projektet och skapa en pull request

### Bidrag är välkomna!
Särskilt intressant:
- Nya expert-providers (fler svenska källor)
- Förbättrad team name matching
- Testning av scrapers
- Dokumentation

---

Byggt med ❤️ för svenska fotbollsentusiaster
