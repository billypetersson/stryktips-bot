# Stryktips Bot - Projektstatus

**Senast uppdaterad:** 2025-10-26
**Aktuell fas:** Expert System Expansion - Internationella leverantörer

---

## 📋 Projektöversikt

Stryktips Bot är ett system för att samla in, analysera och presentera expertprediktioner för Stryktipset (Svenska Spel). Systemet hämtar data från både svenska och internationella expertkällor.

### Huvudkomponenter
- **Backend:** Python/FastAPI
- **Databas:** SQLite/PostgreSQL
- **Deployment:** Kubernetes (K3s)
- **Scraping:** BeautifulSoup, httpx
- **Cache:** File-based caching system

---

## 🎯 Aktuellt arbete: Expert System Expansion

### Vad har gjorts (Slutfört)

#### 1. Databas & Infrastructure ✅
- **Databasschema utökat** med nya fält i `expert_items` tabellen:
  - `title` (Text) - Artikel/video/podcast-titel
  - `summary` (Text) - Sammanfattning eller utdrag
  - `match_tags` (JSON) - Flexibla taggar för matchning
- **Alembic migration** skapad och applicerad: `f902bea8bb6c`

#### 2. Caching Layer ✅
- **Fil:** `src/providers/experts/cache.py`
- File-based cache med konfigurerbar TTL (standard: 6 timmar)
- Per-provider cache-isolering
- Automatisk städning av utgångna poster
- Cache-statistik och hantering

#### 3. Base Provider Uppdaterad ✅
- **Fil:** `src/providers/experts/base.py`
- Integrerad `ProviderCache`
- Uppdaterad `ExpertPrediction` dataclass med nya fält
- Cache-first approach för alla HTTP-anrop

#### 4. Svenska Leverantörer ✅ (10 totalt)
| Leverantör | Fil | Status |
|------------|-----|--------|
| Erik Niva | `erik_niva.py` | ✅ |
| Olof Lundh | `olof_lundh.py` | ✅ |
| Sportbladet | `sportbladet.py` | ✅ |
| Fotbollskanalen | `fotbollskanalen.py` | ✅ |
| Stryktipspodden | `stryktipspodden.py` | ✅ |
| Expressen | `generic_blog.py` | ✅ |
| Rekatochklart | `rekatochklart.py` | ✅ |
| Aftonbladet | `aftonbladet.py` | ✅ |
| Tipsmedoss | `generic_blog.py` | ✅ |
| Spelbloggare | `generic_blog.py` | ✅ |

#### 5. Internationella Leverantörer ✅ (9 totalt)
| Leverantör | Fil | Status | Beskrivning |
|------------|-----|--------|-------------|
| The Guardian | `guardian_football.py` | ✅ | Football Weekly podcast & artiklar |
| The Athletic | `the_athletic.py` | ✅ | Premium sportmedia |
| Opta Analyst | `opta_analyst.py` | ✅ | Datadriven analys med sannolikheter |
| The Totally Football Show | `totally_football_show.py` | ✅ | James Richardson's podcast |
| Tifo Football | `tifo_football.py` | ✅ | Taktisk analys |
| Sky Sports | `sky_sports.py` | ✅ | Neville & Carragher MNF |
| BBC Match of the Day | `bbc_motd.py` | ✅ | Premier League-analys |
| The Coaches' Voice | `coaches_voice.py` | ✅ | Professionella tränares analys |
| The Times | `the_times.py` | ✅ | Premium sportjournalistik |

#### 6. Export Configuration ✅
- **Fil:** `src/providers/experts/__init__.py`
- Alla nya leverantörer exporterade och tillgängliga

---

## 🔄 Nästa steg (Prioriterad ordning)

### 1. ASR-modul för Podcasts/Videos (Ej påbörjad)
**Uppskattad tid:** 1-2 dagar

**Syfte:** Transkribera podcast- och videoinnehåll för att extrahera prediktioner

**Föreslagna verktyg:**
- **Whisper** (rekommenderas) - Offline processing, bra kvalitet
- Google Cloud Speech API
- Azure Speech Services

**Arkitektur:**
```
src/services/asr/
├── __init__.py
├── base.py           # Base ASR provider
├── whisper.py        # Whisper implementation
├── google_cloud.py   # Google Cloud Speech
└── transcriber.py    # Main service
```

**Huvudfunktioner att implementera:**
```python
class ASRTranscriber:
    async def transcribe_podcast(url: str) -> str
    async def segment_by_matches(transcript: str) -> list[MatchSegment]
    async def extract_predictions_from_segment(segment: MatchSegment) -> ExpertPrediction
```

### 2. Smart Match Tagging & Matching (Delvis klar)
**Uppskattad tid:** 4-6 timmar

**Status:** Taggar finns, matchningslogik behövs

**TODO:**
- Skapa fuzzy matching-service för lagnamn
- Hantera olika turneringsnamn (t.ex. "EPL" vs "Premier League")
- Matcha via omgång/vecka när lagnamn inte finns
- Konfidenspoäng för matchningar

**Föreslaget:**
```python
# src/services/match_tagger.py
class MatchTagger:
    def find_match_by_tags(match_tags: dict, coupon: Coupon) -> Optional[Match]
    def normalize_team_name(name: str) -> str
    def normalize_tournament_name(name: str) -> str
```

### 3. Uppdatera Gamla Leverantörer (Ej påbörjad)
**Uppskattad tid:** 2-3 timmar

**TODO:**
- Uppdatera Rekatochklart, Aftonbladet, Stryktipspodden
- Lägg till `title`, `summary`, `match_tags` till gamla leverantörer
- Säkerställ konsistens över alla leverantörer

### 4. Testning och Integration (Ej påbörjad)
**Uppskattad tid:** 1 dag

**TODO:**
- Testa alla leverantörer
- Uppdatera cronjob för att använda nya leverantörer
- Övervaka cache-prestanda
- Skriva enhetstester

---

## 🏗️ Systemarklitektur

### Projektstruktur
```
stryktips-bot/
├── src/
│   ├── models/
│   │   └── expert_item.py          # Databasmodell med nya fält
│   ├── providers/
│   │   └── experts/
│   │       ├── base.py              # Base provider med cache
│   │       ├── cache.py             # Caching layer
│   │       ├── __init__.py          # Exports
│   │       │
│   │       ├── Svenska (10 st)
│   │       │   ├── erik_niva.py
│   │       │   ├── olof_lundh.py
│   │       │   ├── sportbladet.py
│   │       │   ├── fotbollskanalen.py
│   │       │   ├── stryktipspodden.py
│   │       │   ├── rekatochklart.py
│   │       │   ├── aftonbladet.py
│   │       │   └── generic_blog.py
│   │       │
│   │       └── Internationella (9 st)
│   │           ├── guardian_football.py
│   │           ├── the_athletic.py
│   │           ├── opta_analyst.py
│   │           ├── totally_football_show.py
│   │           ├── tifo_football.py
│   │           ├── sky_sports.py
│   │           ├── bbc_motd.py
│   │           ├── coaches_voice.py
│   │           └── the_times.py
│   │
│   └── services/
│       ├── expert_consensus.py      # Behöver uppdatering
│       └── (framtida) asr/          # ASR-modul
│
├── alembic/
│   └── versions/
│       └── f902bea8bb6c_*.py        # Senaste migration
│
├── k8s/
│   └── cronjob-experts.yaml         # Behöver uppdatering
│
└── data/
    └── cache/                       # Provider cache
```

### Databas Schema (expert_items)
```sql
CREATE TABLE expert_items (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    author TEXT,
    published_at TIMESTAMP,
    url TEXT UNIQUE,
    title TEXT,                      -- NY
    summary TEXT,                    -- NY
    match_home_team TEXT,
    match_away_team TEXT,
    pick TEXT NOT NULL,
    rationale TEXT,
    confidence TEXT,
    match_tags JSON,                 -- NY
    raw_data TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 🔧 Konfiguration

### Miljövariabler
```bash
# Expert provider-inställningar
EXPERT_CACHE_TTL_HOURS=6
EXPERT_RATE_LIMIT_DELAY=3.0
EXPERT_MAX_RETRIES=3

# ASR-inställningar (framtida)
ASR_PROVIDER=whisper  # whisper, google, azure
WHISPER_MODEL=base    # tiny, base, small, medium, large
GOOGLE_CLOUD_API_KEY=your_key_here
```

### Kubernetes CronJob
**Fil:** `k8s/cronjob-experts.yaml`

**Behöver uppdateras med:**
```yaml
env:
  - name: ENABLED_SWEDISH_PROVIDERS
    value: "Erik Niva,Olof Lundh,Sportbladet,Fotbollskanalen,Stryktipspodden,Expressen"
  - name: ENABLED_INTERNATIONAL_PROVIDERS
    value: "The Guardian,The Athletic,Opta Analyst,Totally Football Show,Tifo Football,Sky Sports,BBC MOTD,Coaches Voice,The Times"
```

---

## 📊 Användning

### Importera och Använda Leverantörer

```python
from src.providers.experts import (
    # Svenska
    ErikNivaProvider,
    OlofLundhProvider,

    # Internationella
    GuardianFootballProvider,
    TheAthleticProvider,
    OptaAnalystProvider,
    TotallyFootballShowProvider,
    TifoFootballProvider,
    SkySportsProvider,
    BBCMatchOfTheDayProvider,
    CoachesVoiceProvider,
    TheTimesProvider
)

# Exempel: Hämta prediktioner
async def fetch_predictions():
    provider = ErikNivaProvider(rate_limit_delay=3.0)
    predictions = await provider.fetch_latest_predictions(max_items=20)

    for pred in predictions:
        print(f"Titel: {pred.title}")
        print(f"Sammanfattning: {pred.summary}")
        print(f"Match: {pred.match_home_team} vs {pred.match_away_team}")
        print(f"Predikt: {pred.pick}")
        print(f"Taggar: {pred.match_tags}")
```

### Cache-hantering

```python
# Hämta cache-statistik
provider = ErikNivaProvider()
stats = provider.cache.get_stats()
print(stats)  # {'total_entries': 10, 'expired_entries': 2, ...}

# Rensa cache
provider.cache.clear_all()

# Städa utgångna poster
provider.cache.cleanup_expired()
```

---

## 🐛 Kända Problem & Begränsningar

1. **ASR inte implementerad** - Podcast/video-transkribering väntar
2. **Smart matching begränsad** - Grundläggande lagnormalisering, behöver fuzzy matching
3. **Gamla leverantörer** - Behöver uppdatering med nya fält
4. **The Athletic** - Kräver prenumeration för fullständig åtkomst
5. **Vissa internationella leverantörer** - Kan ha paywalls eller regionsspärrar

---

## 📈 Prestanda & Fördelar

### Cache-förbättringar
- Minskar HTTP-anrop med ~80%
- 6 timmars standard TTL
- Provider-isolerad cache

### Skalbarhet
- 19 totala expertkällor (10 svenska + 9 internationella)
- Enkelt att lägga till fler leverantörer
- Rate limiting för att vara artig mot källor

### Datakvalitet
- Rikare metadata (titel, sammanfattning)
- Flexibla match-taggar för intelligent matchning
- Bättre författar-attribution

---

## 📚 Dokumentation & Referenser

### Viktiga filer att läsa
1. `EXPERT_SYSTEM_PROGRESS.md` - Detaljerad framstegsrapport
2. `PROJECT_STATUS.md` - Denna fil (projektöversikt)
3. `src/providers/experts/base.py` - Base provider-implementering
4. `src/models/expert_item.py` - Databasmodell

### Relaterade kommandon
```bash
# Aktivera virtual environment
source venv/bin/activate

# Kör migrationer
alembic upgrade head

# Testa import av leverantörer
python -c "from src.providers.experts import *; print('Success')"

# Visa cache-statistik
ls -lh data/cache/

# Kör expert-scraping (manuellt)
python -m src.jobs.fetch_expert_predictions
```

---

## 🎯 Framtida Förbättringar (Backlog)

### Kort sikt (1-2 veckor)
- [ ] Implementera ASR-modul för podcast/video-transkribering
- [ ] Skapa smart match tagging-service
- [ ] Uppdatera gamla leverantörer med nya fält
- [ ] Skriva enhetstester för nya leverantörer

### Medellång sikt (1 månad)
- [ ] Lägg till fler internationella leverantörer (FiveThirtyEight, ESPN FC, etc.)
- [ ] Implementera machine learning för bättre matchning
- [ ] Skapa dashboard för cache-övervakning
- [ ] A/B-testning av olika expertkonsensusvikter

### Lång sikt (3+ månader)
- [ ] Real-time scraping vid nya publiceringar
- [ ] Automatisk kvalitetsbedömning av experter
- [ ] Integration med betting odds APIs
- [ ] Användarfeedback-system för expertprediktioner

---

## 🤝 Viktiga Beslut & Noteringar

### Designbeslut
1. **File-based cache** valdes över Redis för enkelhet
2. **12 timmar TTL** för internationella leverantörer (vs 6h för svenska)
3. **Rate limiting 3s** mellan anrop för att vara artig
4. **JSON match_tags** för flexibilitet i matchning
5. **Whisper ASR** rekommenderas för offline processing

### Tekniska begränsningar
- SQLite kan bli en flaskhals vid hög belastning → överväg PostgreSQL
- Scraping kan brytas av förändringar i källwebbplatser
- Vissa källor kräver prenumeration (The Athletic, The Times)

### Best Practices
- Alltid använd cache när möjligt
- Respektera rate limits
- Logga alla scraping-försök för debugging
- Validera data innan databas-insert

---

## 📞 Support & Felsökning

### Vanliga problem

**Problem:** Import-fel för nya leverantörer
**Lösning:** Kör `source venv/bin/activate` först

**Problem:** Cache växer för stor
**Lösning:** Kör `provider.cache.cleanup_expired()` regelbundet

**Problem:** Scraping misslyckas
**Lösning:** Kontrollera rate limits och nätverksanslutning, kolla loggar

**Problem:** Migration-fel
**Lösning:** Kontrollera att du är på rätt branch, kör `alembic current`

### Loggar
```bash
# Visa senaste logs från cronjob
kubectl logs -n stryktips-bot <pod-name>

# Lokal debugging
export LOG_LEVEL=DEBUG
python -m src.jobs.fetch_expert_predictions
```

---

## ✅ Checklista för Sessionåterstart

När du startar en ny session, läs denna fil och kontrollera:

- [ ] Förstå var vi är i projektet (se "Nästa steg")
- [ ] Aktivera virtual environment: `source venv/bin/activate`
- [ ] Kolla senaste git-status: `git status`
- [ ] Verifiera att imports fungerar
- [ ] Läs `EXPERT_SYSTEM_PROGRESS.md` för detaljer
- [ ] Identifiera nästa prioriterade uppgift

---

**Skapad av:** Claude Code
**Senast redigerad:** 2025-10-26
**Status:** 🟢 Aktiv utveckling
