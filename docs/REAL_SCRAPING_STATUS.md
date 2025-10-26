# Status: Implementering av Riktig Scraping

## Sammanfattning

Svenska Spel API-integration är **delvis implementerad** och klar att testas när kupong öppnar (ca 20:00 ikväll).

## Vad som är klart ✅

### 1. API Endpoint Identifierad
- **Fungerande endpoint**: `https://api.spela.svenskaspel.se/draw/1/stryktipset/draws`
- Status: **Verifierad** och svarar med 200 OK
- Just nu: Returnerar `{"draws": []}` eftersom kupong inte är öppen
- När öppen: Kommer returnera array med draw-objekt

### 2. Uppdaterad Scraper
**Fil**: `src/scrapers/svenska_spel.py`

Har nu tre strategier i fallback-ordning:
1. **API-först** (ny implementation)
   - Använder verifierad endpoint
   - Flexibel parsing som hanterar olika fältnamn
   - Detaljerad loggning för debugging

2. **Playwright-backup** (förberedd)
   - Fallback om API inte fungerar
   - Använder browser automation

3. **Mock data** (befintlig)
   - Sista alternativ för testning

### 3. Flexibel API Parser
**Metoder**:
- `_fetch_from_api()` - Hämtar från API med korrekta headers
- `_parse_api_response()` - Parsar draw-objekt (flera möjliga fältnamn)
- `_parse_event()` - Parsar enskilda matcher (flexibel struktur)

**Funktioner**:
- Hanterar olika fältnamn: `homeTeam`/`home`, `drawDate`/`date`, etc.
- Parsar nested objekt (t.ex. `{"name": "Arsenal"}`)
- Konverterar streckprocent från olika format
- Detaljerad loggning av struktur för debugging

### 4. Test Script
**Fil**: `scripts/test_api_structure.py`

Kör detta ikväll när kupong öppnar för att:
- Visa fullständig API response struktur
- Spara rådata till `api_response_raw.json`
- Spara första match till `api_first_event.json`
- Identifiera exakta fältnamn för uppdatering av parser

## Vad som behöver göras 🔧

### Ikväll (när kupong öppnar ~20:00)

1. **Kör test script**:
   ```bash
   source venv/bin/activate
   python scripts/test_api_structure.py
   ```

2. **Granska output**:
   - Vilka keys finns i draw-objektet?
   - Hur ser event/match-strukturen ut?
   - Var finns streckprocent (distribution)?
   - Hur ser team-namn ut (string eller dict)?

3. **Uppdatera parser om nödvändigt**:
   Baserat på test output, justera i `src/scrapers/svenska_spel.py`:
   - `_parse_api_response()` - Rätt fältnamn för draw
   - `_parse_event()` - Rätt fältnamn för matcher

4. **Testa full pipeline**:
   ```bash
   # Ta bort gammal mock-data
   rm -f stryktips.db
   python scripts/init_db.py

   # Kör uppdatering med riktig data
   python -m src.jobs.update_coupon
   ```

5. **Verifiera i webb-UI**:
   - Öppna http://192.168.1.25:8000
   - Kontrollera att matcher visas korrekt
   - Kolla att lag-namn är rätt
   - Verifiera streckprocent

## Förväntad API Struktur (gissning)

Baserat på vanliga mönster, förväntad struktur är troligen:

```json
{
  "draws": [
    {
      "drawNumber": 44,
      "drawDate": "2025-11-02T15:00:00Z",
      "drawState": "open",
      "jackpot": {
        "amount": 10000000,
        "currency": "SEK"
      },
      "events": [
        {
          "eventNumber": 1,
          "homeTeam": {
            "name": "Arsenal",
            "id": 123
          },
          "awayTeam": {
            "name": "Liverpool",
            "id": 456
          },
          "startTime": "2025-11-02T13:00:00Z",
          "distribution": {
            "home": 45.2,
            "draw": 28.3,
            "away": 26.5
          }
        },
        ...13 matcher totalt...
      ]
    }
  ]
}
```

**Men**: Detta är **gissning**! Verklig struktur kan vara helt annorlunda.
Därför har vi byggt flexibel parsing som testar flera alternativ.

## Alternativa Fältnamn som Parsen Hanterar

Parser letar efter följande alternativ (i prioritetsordning):

### Draw-nivå:
- **Draw number**: `drawNumber` → `drawId` → `number`
- **Draw date**: `drawDate` → `date` → `drawTime`
- **Events/matches**: `events` → `matches`
- **Jackpot**: `jackpot` → `estimatedJackpot`

### Event-nivå:
- **Home team**: `homeTeam` → `home`
- **Away team**: `awayTeam` → `away`
- **Kickoff**: `startTime` → `kickoffTime` → `matchTime`
- **Distribution**: `distribution` → `outcome`

### Distribution-nivå:
- **Home**: `home` → `1` → `H`
- **Draw**: `draw` → `X` → `D`
- **Away**: `away` → `2` → `A`

## Om API Inte Fungerar

### Alternativ 1: Playwright Scraping
Redan förberett i koden. Om API misslyckas, provas automatiskt:
1. Öppnar browser (Chromium)
2. Renderar JavaScript
3. Extraherar data från DOM

**Status**: Playwright installerad, men selektorer behöver hittas när kupong är öppen.

### Alternativ 2: Skapa Github Issue
Om varken API eller Playwright fungerar:
1. Spara `api_response_raw.json` (om API svarar)
2. Spara `stryktipset_page.html` och `stryktipset_screenshot.png` (om Playwright körs)
3. Skapa issue med dessa filer
4. Vi kan då analysera strukturen och uppdatera koden

## Filer att Granska

När du testar ikväll, kolla dessa filer:

1. **Scraper-logik**: `src/scrapers/svenska_spel.py`
2. **Test script**: `scripts/test_api_structure.py`
3. **Playwright backup**: `src/scrapers/svenska_spel_playwright.py`
4. **Guiden**: `docs/SCRAPING_GUIDE.md`

## Debugging Tips

### Om parsingen misslyckas:
Kolla loggarna - detaljerad info finns där:
```bash
# Kör med DEBUG-läge
LOG_LEVEL=DEBUG python -m src.jobs.update_coupon
```

Parser loggar:
- `"Parsing draw with keys: [...]"` - Visar vilka fält draw har
- `"Failed to parse event X"` - Visar vilken match som failar
- `"No matches found in API response"` - API-struktur matchar inte förväntningar

### Om streckprocent saknas:
Kolla `api_first_event.json` efter fält som innehåller:
- "distribution", "outcome", "percentage"
- Nummer som summerar till ~100
- Fält med keys: "1", "X", "2" eller "H", "D", "A"

## Nästa Sprint (efter riktig data fungerar)

1. **Implementera riktiga odds-scrapers** (Bet365, Unibet, etc.)
2. **Implementera expert-scrapers** (Aftonbladet, Expressen, SVT)
3. **Förbättra värdeberäkning** med historisk data
4. **Backtesting** av radgenerering

## Kontakt & Support

Om du stöter på problem:
1. Spara alla genererade JSON-filer
2. Kopiera logg-output
3. Ta screenshot av webb-UI om något ser konstigt ut
4. Vi kan då felsöka baserat på verklig data

---

**Status**: Redo för test ikväll! 🚀
**Nästa steg**: Kör `python scripts/test_api_structure.py` när kupong öppnar
