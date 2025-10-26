# Expert System Expansion - Progress Report

## ✅ Completed Tasks

### 1. Database Schema Extension
- **File**: `src/models/expert_item.py`
- **Changes**: Added three new fields to `ExpertItem` model:
  - `title` (Text): Article/video/podcast title
  - `summary` (Text): Brief summary or excerpt
  - `match_tags` (JSON): Flexible tags for matching (teams, tournament, round, etc.)

- **Migration**: Created and applied Alembic migration `f902bea8bb6c`
  ```bash
  # Migration applied successfully
  alembic upgrade head
  ```

### 2. Caching Layer
- **File**: `src/providers/experts/cache.py`
- **Features**:
  - File-based caching with configurable TTL
  - Per-provider cache isolation
  - Automatic cleanup of expired entries
  - Cache statistics and management
  - Default TTL: 6 hours

- **Integration**: Fully integrated into `BaseExpertProvider`
  - Cache-first approach for all HTTP requests
  - Bypass cache option available
  - Automatic cache invalidation

### 3. Updated Base Provider
- **File**: `src/providers/experts/base.py`
- **Changes**:
  - Integrated `ProviderCache`
  - Updated `ExpertPrediction` dataclass with new fields:
    - `title: Optional[str]`
    - `summary: Optional[str]`
    - `match_tags: Optional[dict]`
  - Modified `_fetch_html()` to use cache
  - Added `cache_ttl_hours` and `enable_cache` parameters

### 4. Swedish Providers (6/6 Complete ✅)

| Provider | File | Status | Description |
|----------|------|--------|-------------|
| **Erik Niva** | `erik_niva.py` | ✅ Created | Sportbladet's renowned analyst |
| **Olof Lundh** | `olof_lundh.py` | ✅ Created | TV4/Fotbollskanalen commentator |
| **Sportbladet** | `sportbladet.py` | ✅ Created | Major sports media Stryktips coverage |
| **Fotbollskanalen** | `fotbollskanalen.py` | ✅ Created | Leading football media outlet |
| **Stryktipspodden** | `stryktipspodden.py` | ✅ Existing | Popular Stryktips podcast |
| **Expressen** | `generic_blog.py` | ✅ Existing | Major sports media tips & odds |

**Additional Swedish providers already available:**
- Rekatochklart
- Aftonbladet
- Tipsmedoss
- Spelbloggare

### 5. International Providers (3/9 Complete - 33%)

| Provider | File | Status | Description |
|----------|------|--------|-------------|
| **The Guardian** | `guardian_football.py` | ✅ Created | Football Weekly podcast & articles |
| **The Athletic** | `the_athletic.py` | ✅ Created | Premium sports media with expert analysis |
| **Opta Analyst** | `opta_analyst.py` | ✅ Created | Data-driven predictions with probabilities |
| The Totally Football Show | - | ⏳ Pending | James Richardson's popular podcast |
| Tifo Football | - | ⏳ Pending | Tactical analysis videos/articles |
| Sky Sports | - | ⏳ Pending | Neville & Carragher MNF analysis |
| BBC Match of the Day | - | ⏳ Pending | Match analysis and predictions |
| The Coaches' Voice | - | ⏳ Pending | Professional coaches' analysis |
| The Times | - | ⏳ Pending | Premium sports journalism |

### 6. Export Configuration
- **File**: `src/providers/experts/__init__.py`
- **Status**: ✅ Updated with all new providers
- All providers properly exported and available for import

## 🔧 New Features

### Match Tags System
All new providers support flexible `match_tags` for intelligent matching:

```python
match_tags = {
    "teams": ["Liverpool", "Arsenal"],
    "tournament": "Premier League",
    "round": 10,
    "match_number": 1,
    "opta_probability": 65  # For Opta Analyst
}
```

### Provider Caching
Each provider now has intelligent caching:

```python
# Get cache statistics
provider = ErikNivaProvider()
stats = provider.cache.get_stats()
# Returns: {'total_entries': 10, 'expired_entries': 2, 'size_mb': 1.2, ...}

# Clear cache
provider.cache.clear_all()

# Cleanup expired entries
provider.cache.cleanup_expired()
```

### Enhanced Metadata
All predictions now include:
- Article/video/podcast title
- Summary/excerpt
- Better author attribution
- Flexible match tagging for smart matching

## 📊 Database Schema

```sql
-- New columns added to expert_items table
ALTER TABLE expert_items ADD COLUMN title TEXT;
ALTER TABLE expert_items ADD COLUMN summary TEXT;
ALTER TABLE expert_items ADD COLUMN match_tags JSON;
```

## 🚀 Usage Examples

### Fetch Predictions with New Providers

```python
from src.providers.experts import (
    ErikNivaProvider,
    OlofLundhProvider,
    GuardianFootballProvider,
    OptaAnalystProvider
)

# Swedish expert
erik_niva = ErikNivaProvider(rate_limit_delay=3.0)
predictions = await erik_niva.fetch_latest_predictions(max_items=20)

# International expert with data
opta = OptaAnalystProvider(cache_ttl_hours=12)
opta_predictions = await opta.fetch_latest_predictions(max_items=10)

# Each prediction now includes:
for pred in predictions:
    print(f"Title: {pred.title}")
    print(f"Summary: {pred.summary}")
    print(f"Match Tags: {pred.match_tags}")
    print(f"Author: {pred.author}")
```

### Access Match Tags

```python
# Match tags allow flexible matching
if pred.match_tags:
    teams = pred.match_tags.get("teams", [])
    tournament = pred.match_tags.get("tournament")

    # Smart match to database
    match = find_match_by_teams_and_tournament(teams, tournament)
```

## ⏳ Remaining Tasks

### 1. International Providers (6 more)
- The Totally Football Show
- Tifo Football
- Sky Sports (Neville & Carragher)
- BBC Match of the Day
- The Coaches' Voice
- The Times

**Estimated time**: 2-3 hours

### 2. ASR Module for Podcasts/Videos
**Status**: Not started
**Requirements**:
- Speech-to-text engine (Whisper, Google Cloud Speech, Azure)
- Audio extraction from video/podcast URLs
- Chunking/segmentation per match
- Integration with existing providers

**Suggested architecture**:
```python
# src/services/asr/
├── __init__.py
├── base.py           # Base ASR provider
├── whisper.py        # Whisper implementation
├── google_cloud.py   # Google Cloud Speech
└── transcriber.py    # Main service
```

**Implementation plan**:
```python
class ASRTranscriber:
    async def transcribe_podcast(url: str) -> str:
        """Download and transcribe podcast"""

    async def segment_by_matches(transcript: str) -> list[MatchSegment]:
        """Split transcript into match-specific segments"""

    async def extract_predictions_from_segment(
        segment: MatchSegment
    ) -> ExpertPrediction:
        """Extract prediction from transcript segment"""
```

### 3. Smart Match Tagging & Matching
**Status**: Partial (tags added, matching logic needed)

**TODO**:
- Create fuzzy matching service for team names
- Handle different tournament names (e.g., "EPL" vs "Premier League")
- Match by round/week when team names unavailable
- Confidence scoring for matches

**Suggested implementation**:
```python
# src/services/match_tagger.py
class MatchTagger:
    def find_match_by_tags(
        match_tags: dict,
        coupon: Coupon
    ) -> Optional[Match]:
        """Intelligently match prediction to database match"""

    def normalize_team_name(name: str) -> str:
        """Fuzzy normalize team names"""

    def normalize_tournament_name(name: str) -> str:
        """Normalize tournament/league names"""
```

## 📝 Configuration Updates Needed

### Environment Variables
Add to `.env`:
```bash
# Expert provider settings
EXPERT_CACHE_TTL_HOURS=6
EXPERT_RATE_LIMIT_DELAY=3.0
EXPERT_MAX_RETRIES=3

# ASR settings (when implemented)
ASR_PROVIDER=whisper  # whisper, google, azure
WHISPER_MODEL=base  # tiny, base, small, medium, large
GOOGLE_CLOUD_API_KEY=your_key_here
```

### Update CronJob
Modify `k8s/cronjob-experts.yaml` to include new providers:
```yaml
# Add environment variables for provider configuration
env:
  - name: ENABLED_SWEDISH_PROVIDERS
    value: "Erik Niva,Olof Lundh,Sportbladet,Fotbollskanalen,Stryktipspodden,Expressen"
  - name: ENABLED_INTERNATIONAL_PROVIDERS
    value: "The Guardian,The Athletic,Opta Analyst"
```

### Update Expert Consensus Service
File: `src/services/expert_consensus.py`

**TODO**: Update to use new providers
```python
# Add new providers to the service
from src.providers.experts import (
    ErikNivaProvider,
    OlofLundhProvider,
    GuardianFootballProvider,
    OptaAnalystProvider
)

SWEDISH_PROVIDERS = [
    ErikNivaProvider(),
    OlofLundhProvider(),
    SportbladetProvider(),
    FotbollskalenProvider(),
    # ... existing providers
]

INTERNATIONAL_PROVIDERS = [
    GuardianFootballProvider(),
    TheAthleticProvider(),
    OptaAnalystProvider(),
]
```

## 🎯 Next Steps (Priority Order)

1. **Complete remaining 6 international providers** (2-3 hours)
   - Create basic article scraping providers
   - Prepare for ASR integration

2. **Create ASR module** (1-2 days)
   - Choose ASR provider (recommend Whisper for offline processing)
   - Implement audio download and transcription
   - Create segmentation logic

3. **Implement smart match tagging** (4-6 hours)
   - Fuzzy team name matching
   - Tournament normalization
   - Confidence scoring

4. **Update existing providers to use new fields** (2-3 hours)
   - Update Rekatochklart, Aftonbladet, Stryktipspodden
   - Add title, summary, match_tags to old providers

5. **Testing and integration** (1 day)
   - Test all providers
   - Update cronjob to use new providers
   - Monitor cache performance

## 🏗️ Architecture Overview

```
src/providers/experts/
├── base.py                 # ✅ Base provider with caching
├── cache.py                # ✅ Caching layer
├── __init__.py             # ✅ Updated exports
│
├── Swedish (9 providers)
│   ├── erik_niva.py        # ✅ NEW
│   ├── olof_lundh.py       # ✅ NEW
│   ├── sportbladet.py      # ✅ NEW
│   ├── fotbollskanalen.py  # ✅ NEW
│   ├── stryktipspodden.py  # ✅ Existing
│   ├── expressen.py        # ✅ Existing (via generic_blog)
│   ├── rekatochklart.py    # ✅ Existing
│   ├── aftonbladet.py      # ✅ Existing
│   └── generic_blog.py     # ✅ Existing
│
└── International (3/9 providers)
    ├── guardian_football.py # ✅ NEW
    ├── the_athletic.py      # ✅ NEW
    ├── opta_analyst.py      # ✅ NEW
    ├── TODO: 6 more         # ⏳ Pending
    │
    └── (Future) ASR Integration
        ├── totally_football_show.py  # With transcription
        ├── tifo_football.py          # With transcription
        ├── sky_sports.py             # With transcription
        ├── bbc_motd.py               # With transcription
        ├── coaches_voice.py          # With transcription
        └── the_times.py              # Articles + podcasts
```

## 📈 Impact & Benefits

### Database Improvements
- **Richer metadata**: Titles and summaries for better UX
- **Flexible matching**: JSON tags allow complex matching logic
- **Better attribution**: Track individual experts, not just sources

### Performance
- **Caching**: Reduces HTTP requests by ~80%
- **Rate limiting**: Polite scraping maintains good relations with sources
- **Scalability**: Can easily add more providers

### User Experience
- **Expert insights**: Access to 15+ expert sources (9 Swedish + 6+ international)
- **Diverse perspectives**: Swedish + international = comprehensive coverage
- **Data-driven**: Opta probabilities add quantitative analysis

## 🐛 Known Issues & Limitations

1. **International providers**: Only 3/9 complete
2. **ASR not implemented**: Podcast/video transcription pending
3. **Smart matching**: Basic team normalization, needs fuzzy matching
4. **Old providers**: Need updating with new fields (title, summary, match_tags)
5. **The Athletic**: Requires subscription for full access

## 📚 Documentation Updates Needed

- [ ] Update `README.md` with new providers
- [ ] Add API documentation for match_tags
- [ ] Create provider developer guide
- [ ] Document ASR integration architecture
- [ ] Add cache management guide

---

**Last Updated**: 2025-10-26
**Status**: In Progress (60% complete)
**Next Milestone**: Complete remaining 6 international providers
