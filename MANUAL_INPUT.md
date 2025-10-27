# Manuell Input av Stryktipsrad

Om Svenska Spel-scrapern inte fungerar kan du mata in stryktipsraden manuellt.

## 📝 Metod 1: Textfil (Enklast!)

1. Redigera `example_coupon.txt` med rätt matcher och streckprocent:

```
1. Liverpool - Aston Villa | 53 21 26
2. Tottenham - Man City | 30 25 45
3. Burnley - Newcastle | 35 28 37
...
```

Format: `Matchnummer. Hemmalag - Bortalag | hem% oavgjort% borta%`

2. Kör scriptet:

```bash
source venv/bin/activate
python scripts/manual_coupon_input.py --week 43 --year 2025 --file example_coupon.txt --run-analysis
```

## 💻 Metod 2: Interaktiv Input

Kör scriptet och mata in matcher en och en:

```bash
source venv/bin/activate
python scripts/manual_coupon_input.py --week 43 --year 2025 --run-analysis
```

Du kommer bli frågad om varje match:
```
Match 1: Liverpool - Aston Villa | 53 21 26
Match 2: Tottenham - Man City | 30 25 45
...
```

## 📊 Metod 3: Direkt från Kommandorad

```bash
python scripts/manual_coupon_input.py --week 43 --year 2025 \
  --text "1. Liverpool - Aston Villa | 53 21 26
2. Tottenham - Man City | 30 25 45" \
  --run-analysis
```

## ⚙️ Flaggor

- `--week` (krävs): Veckonummer
- `--year` (valfritt): År (standard: nuvarande år)
- `--file`: Läs från textfil
- `--text`: Läs från textsträng
- `--run-analysis`: Kör hela analyspipelinen automatiskt
  - Hämtar odds från bookmakersidor
  - Hämtar expertprediktioner
  - Beräknar värde
  - Genererar föreslagna rader

## 🚀 Efter Input

Scriptet kommer:
1. ✅ Skapa ny kupong i databasen
2. ✅ Lägga till alla matcher
3. ✅ (Om `--run-analysis`) Köra hela analysen
4. ✅ Visa resultat

Starta sedan webbservern:

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Gå till http://localhost:8000 eller http://stryktips.local

## 📥 Hämta Data från Svenska Spel (Manuellt)

1. Gå till https://spela.svenskaspel.se/stryktipset
2. Kopiera matcherna och streckprocenten
3. Fyll i `example_coupon.txt`
4. Kör scriptet

## 🔧 Felsökning

**Problem**: Import-fel
**Lösning**: Aktivera virtual environment först: `source venv/bin/activate`

**Problem**: Fel format
**Lösning**: Kontrollera att formatet är: `Nummer. Hemmalag - Bortalag | hem% oavgjort% borta%`

**Problem**: Kupong existerar redan
**Lösning**: Scriptet deaktiverar automatiskt gamla kuponger, så detta borde inte hända

## 💡 Tips

- Streckprocenten ska alltid summera till ~100
- Du kan mata in 1-13 matcher (typiskt 13)
- Lagnamn kan innehålla mellanslag (t.ex. "Man United")
- Procenten är heltal eller decimaltal (53 eller 53.5)
