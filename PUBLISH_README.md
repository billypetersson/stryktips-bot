# Publicera Liverpool - Aston Villa till http://stryktips.local/

## Snabbstart

Kör detta kommando för att publicera ALLT (match, odds, analys och systemförslag) till k3s:

```bash
cd /home/admbilly/stryktips-bot
./publish_to_k3s.sh
```

Detta kommer automatiskt att:
1. ✅ Inaktivera vecka 43
2. ✅ Aktivera vecka 44
3. ✅ Lägga till Liverpool - Aston Villa
4. ✅ Lägga till odds (1=1.57, X=4.75, 2=5.60)
5. ✅ Lägga till analysen (rekommendation: 1, värde: 1.22)
6. ✅ Lägga till systemförslag (2 rader)
7. ✅ Verifiera att allt finns i databasen
8. ✅ Testa att hemsidan fungerar

## Vad händer efter publicering?

När scriptet är klart kan du gå till **http://stryktips.local/** och se:

### Startsida
- **Vecka 44, 2025** kupong
- **1. Liverpool - Aston Villa**
- **Rekommendation: 1** (hemmavinst)

### Analys-sida (klicka på kupongen)
- **Värdeanalys:**
  - Genomsnittliga odds: 1=1.57, X=4.75, 2=5.60
  - Beräknade sannolikheter: 1=62.1%, X=20.5%, 2=17.4%
  - Värde: 1=1.22 ← **+22% value!**

- **Systemförslag:**
  - **Rad 1:** Alla "1" (kostnad: 1x, EV: 0.09)
  - **Rad 2:** "1X" på match 1, resten "1" (kostnad: 2x, EV: 0.17) ← **Rekommenderad!**

### Highlights
- 🎯 **Liverpool är en stark värdefavorit**
- 📊 **Svenska folket understreckar** (51% vs 62.1% beräknat)
- 💰 **Systemrad 2 har högre förväntat värde** trots dubbel kostnad

## Felsökning

### Om Liverpool inte syns på hemsidan:
1. **Rensa browser-cache:** Tryck Ctrl+F5 på hemsidan
2. **Vänta 30 sekunder:** Ingress-cachen kan behöva uppdateras
3. **Kolla logs:**
   ```bash
   sudo k3s kubectl logs -n stryktips -l app=stryktips-bot --tail=50
   ```

### Om du får fel:
- **"Permission denied":** Scriptet kräver sudo-rättigheter
- **"Pod not found":** K3s-klustret kanske inte körs, starta det med `sudo k3s kubectl get pods -n stryktips`

## Manuell publicering (om scriptet inte fungerar)

```bash
# 1. Kopiera SQL-fil
sudo k3s kubectl cp publish_to_k3s_complete.sql stryktips/$(sudo k3s kubectl get pods -n stryktips -l app=postgres -o jsonpath='{.items[0].metadata.name}'):/tmp/publish_complete.sql

# 2. Kör SQL
sudo k3s kubectl exec -n stryktips $(sudo k3s kubectl get pods -n stryktips -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U stryktips -d stryktips -f /tmp/publish_complete.sql

# 3. Verifiera
curl http://stryktips.local/ | grep Liverpool
```

## Databaser

Projektet använder **två databaser**:

1. **SQLite** (`stryktips.db`) - Lokal utveckling på localhost:8000
2. **PostgreSQL** (k3s) - Produktion på http://stryktips.local/

Scriptet `publish_to_k3s.sh` synkroniserar från SQLite till PostgreSQL.

## Nästa steg

För att lägga till fler matcher:
1. Kör `python add_test_match.py` med ny matchdata
2. Kör `python analyze_liverpool.py` för att få analys
3. Kör `./publish_to_k3s.sh` för att publicera

Eller använd uppdateringsjobbet:
```bash
sudo k3s kubectl create job --from=cronjob/stryktips-update manual-update-$(date +%s) -n stryktips
```
