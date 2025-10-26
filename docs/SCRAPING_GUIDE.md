# Guide: Implementera Riktiga Scrapers

## Problem med Svenska Spel

Svenska Spels webbplats (https://spela.svenskaspel.se/stryktipset) är en modern JavaScript-driven Single Page Application (SPA). Detta innebär:

1. **HTML innehåller ingen data** - Sidan är tom tills JavaScript körs
2. **API:et är skyddat** - Kräver speciella headers, tokens eller sessioner
3. **Rate limiting** - API:et verkar ha timeout/rate limiting

## Lösningar

### Alternativ 1: Browser Automation (Rekommenderat)

Använd Playwright eller Selenium för att köra en riktig webbläsare som renderar JavaScript.

#### Installation:

```bash
pip install playwright
playwright install chromium
```

#### Exempel-implementation:

```python
# src/scrapers/svenska_spel_playwright.py
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def scrape_stryktipset():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Gå till Stryktips-sidan
        await page.goto('https://spela.svenskaspel.se/stryktipset')

        # Vänta tills matchdata laddats
        await page.wait_for_selector('.event-row', timeout=10000)

        # Hämta matcher
        matches = await page.eval_on_selector_all('.event-row', '''
            elements => elements.map(el => ({
                home_team: el.querySelector('.home-team')?.textContent,
                away_team: el.querySelector('.away-team')?.textContent,
                kickoff: el.querySelector('.kickoff-time')?.textContent,
            }))
        ''')

        await browser.close()
        return matches
```

**För-/nackdelar:**
- ✅ Fungerar alltid - renderar sidan som en riktig användare
- ✅ Inga API-tokens behövs
- ❌ Långsammare (2-5 sekunder per scrape)
- ❌ Kräver mer resurser (Chromium browser)

### Alternativ 2: Reverse-Engineer API

Hitta de riktiga API-anropen som webbplatsen gör.

#### Steg:

1. **Öppna Chrome DevTools** (F12) på https://spela.svenskaspel.se/stryktipset
2. **Gå till Network-fliken**
3. **Filtrera på "Fetch/XHR"**
4. **Ladda om sidan** och leta efter API-anrop

#### Vad att leta efter:

```
# Exempel på möjliga endpoints:
https://api.svenskaspel.se/draw/1/stryktipset/draws/latest
https://api.svenskaspel.se/game/stryktipset/...
https://www.svenskaspel.se/api/...

# Kolla headersen i Request:
Authorization: Bearer ...
X-Client-Id: ...
Cookie: ...
```

#### Implementation:

```python
async def fetch_from_real_api(self):
    headers = {
        'User-Agent': 'Mozilla/5.0...',
        'Authorization': 'Bearer YOUR_TOKEN',  # Hittas i DevTools
        'X-Client-Id': 'web-client',
        'Referer': 'https://spela.svenskaspel.se/',
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://api.svenskaspel.se/actual/endpoint',
            headers=headers
        )
        return response.json()
```

**För-/nackdelar:**
- ✅ Snabbt (< 1 sekund)
- ✅ Lätt att underhålla om API:et är stabilt
- ❌ API kan ändras när som helst
- ❌ Kan kräva autentisering
- ❌ Risk för IP-blockering vid för många requests

### Alternativ 3: Använda Odds-Jämförelsesajter

Istället för Svenska Spel, hämta data från odds-jämförelsesajter som:

- **Oddsportal** (oddsportal.com)
- **Flashscore** (flashscore.com)
- **TheOddsAPI** (the-odds-api.com) - Kommersiell API-tjänst

#### Exempel med TheOddsAPI:

```python
# Kräver API-nyckel (gratis tier finns)
async def fetch_from_odds_api(self):
    api_key = 'YOUR_API_KEY'
    url = f'https://api.the-odds-api.com/v4/sports/soccer_sweden_allsvenskan/odds'

    params = {
        'apiKey': api_key,
        'regions': 'eu',
        'markets': 'h2h',
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()
```

**För-/nackdelar:**
- ✅ Officiella API:er med dokumentation
- ✅ Stabila, supporterade
- ✅ Ofta gratis tier tillgänglig
- ❌ Kostar pengar för högre usage
- ❌ Kanske inte har exakt Stryktips-matcher

### Alternativ 4: RSS/Atom Feeds

Vissa sporttjänster publicerar matcher via RSS.

```python
import feedparser

def fetch_from_rss(self):
    feed = feedparser.parse('https://example.com/stryktips.rss')
    for entry in feed.entries:
        # Parse entry data
        pass
```

## Rekommenderad Approach för Produktion

**Hybrid-lösning:**

1. **Primär**: Playwright/Selenium (kör 1 gång per vecka, fredag morgon)
2. **Backup**: RSS-feeds eller odds-sajter
3. **Fallback**: Mock data (för testning)

```python
async def scrape(self):
    try:
        return await self._scrape_with_playwright()
    except Exception as e:
        logger.error(f"Playwright failed: {e}")
        try:
            return await self._scrape_from_odds_api()
        except Exception as e:
            logger.error(f"Odds API failed: {e}")
            return await self._fetch_mock_coupon()
```

## Juridiska Överväganden

⚠️ **VIKTIGT**:

1. **Läs användarvillkoren** för Svenska Spel och andra sajter
2. **Respektera robots.txt**
3. **Använd rimlig rate limiting** (1 request per minut är ofta OK)
4. **Överväg att maila** Svenska Spel och fråga om det finns ett officiellt API
5. **För personligt bruk** är det oftast OK, men för kommersiellt bruk krävs tillstånd

## Nästa Steg

1. Välj en av lösningarna ovan
2. Implementera i `src/scrapers/svenska_spel.py`
3. Testa med `python -m src.jobs.update_coupon`
4. Konfigurera CronJob för automatisk uppdatering

## Support

Om du behöver hjälp:
- Kolla Svenska Spels utvecklardokumentation
- Sök efter "Svenska Spel API" på GitHub
- Community-projekt kanske har liknande lösningar
