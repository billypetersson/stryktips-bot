# Stryktips Bot - K3s Deployment Guide

## ✅ Deployment Status

Stryktips-bot är nu **deployad och kör i ditt k3s cluster**! 🎉

## Deployment Sammanfattning

### Cluster Information
- **K8s Version**: v1.33.5+k3s1
- **Node**: peterssontech
- **Registry**: localhost:30500 (lokalt k3s registry)
- **Namespace**: stryktips

### Deployade Komponenter

| Komponent | Status | Replicas | Image |
|-----------|--------|----------|-------|
| PostgreSQL | ✅ Running | 1 | postgres:16-alpine |
| Stryktips App | ✅ Running | 1 | localhost:30500/stryktips-bot:latest |
| CronJob | ✅ Scheduled | - | localhost:30500/stryktips-bot:latest |

### CronJob Schema
- **Schema**: Varje söndag kl 20:00 (Europe/Stockholm timezone)
- **Cron**: `0 20 * * 0`
- **Timezone**: `Europe/Stockholm`
- **Första körning**: Nästa söndag 20:00

### Nätverkskonfiguration
- **Service**: stryktips-service (ClusterIP: 10.43.50.143, port 80)
- **Ingress**: stryktips-ingress (Host: stryktips.local)
- **Database**: postgres-service (Headless service, port 5432)

## Åtkomst till Applikationen

### Via Ingress (Rekommenderat)

För att komma åt applikationen från din desktop:

1. **Lägg till i /etc/hosts** (eller C:\Windows\System32\drivers\etc\hosts på Windows):
   ```
   192.168.1.25  stryktips.local
   ```

2. **Öppna i webbläsare**:
   ```
   http://stryktips.local
   ```

### Via cURL (Testning)
```bash
curl -H "Host: stryktips.local" http://192.168.1.25/
```

## Verifiering av Deployment

### Kolla status för alla komponenter:
```bash
sudo k3s kubectl get all -n stryktips
```

### Kolla logs från applikation:
```bash
sudo k3s kubectl logs -n stryktips -l app=stryktips-bot --tail=50
```

### Kolla CronJob status:
```bash
sudo k3s kubectl get cronjobs -n stryktips
```

### Kolla nästa schemalagda körning:
```bash
sudo k3s kubectl get cronjobs -n stryktips -o wide
```

## Manuell Uppdatering

För att köra en manuell uppdatering av kupongen:

```bash
# Skapa ett Job från CronJob
sudo k3s kubectl create job -n stryktips --from=cronjob/stryktips-updater manual-update-$(date +%s)

# Följ loggar
sudo k3s kubectl logs -n stryktips -l app=stryktips-bot,component=cronjob -f
```

## Database Management

### Initiera databas (redan gjort):
```bash
POD=$(sudo k3s kubectl get pods -n stryktips -l app=stryktips-bot -o jsonpath='{.items[0].metadata.name}')
sudo k3s kubectl exec -n stryktips $POD -- python scripts/init_db.py
```

### Koppla upp mot PostgreSQL direkt:
```bash
sudo k3s kubectl exec -n stryktips -it deployment/postgres -- psql -U stryktips -d stryktips
```

## Uppdatera Applikationen

När du gör ändringar i koden:

### 1. Bygg ny image:
```bash
sudo docker build -t localhost:30500/stryktips-bot:latest .
```

### 2. Pusha till registry:
```bash
sudo docker push localhost:30500/stryktips-bot:latest
```

### 3. Starta om deployment:
```bash
sudo k3s kubectl rollout restart deployment/stryktips-app -n stryktips
```

### 4. Följ rollout:
```bash
sudo k3s kubectl rollout status deployment/stryktips-app -n stryktips
```

## Svenska Spel API Integration

### Status
- ✅ API endpoint identifierad: `https://api.spela.svenskaspel.se/draw/1/stryktipset/draws`
- ✅ Parser uppdaterad med korrekt fältnamn (`drawEvents`)
- ⚠️ Faller tillbaka på mock data när kupong inte är öppen
- 📅 Testa med riktig data ikväll ca 20:00 när kupong öppnar

### Test API när kupong öppnar:
```bash
POD=$(sudo k3s kubectl get pods -n stryktips -l app=stryktips-bot -o jsonpath='{.items[0].metadata.name}')
sudo k3s kubectl exec -n stryktips $POD -- python scripts/test_api_structure.py
```

## Felsökning

### Pod startar inte:
```bash
# Kolla events
sudo k3s kubectl describe pod -n stryktips <pod-name>

# Kolla logs
sudo k3s kubectl logs -n stryktips <pod-name>
```

### Database connection issues:
```bash
# Kolla om postgres körs
sudo k3s kubectl get pods -n stryktips -l app=postgres

# Kolla postgres logs
sudo k3s kubectl logs -n stryktips deployment/postgres
```

### Ingress fungerar inte:
```bash
# Kolla ingress status
sudo k3s kubectl get ingress -n stryktips

# Kolla Traefik logs
sudo k3s kubectl logs -n kube-system deployment/traefik
```

### CPU/Minne problem:
Deployment är satt till 1 replica pga CPU-begränsningar i single-node cluster.

För att öka till 2 replicas (om du har mer resurser):
```bash
sudo k3s kubectl scale deployment stryktips-app -n stryktips --replicas=2
```

## Konfiguration

### ConfigMap (k8s/configmap.yaml):
```yaml
LOG_LEVEL: INFO
DEBUG: "false"
SCRAPE_TIMEOUT: "30"
MAX_HALF_COVERS: "2"
MIN_VALUE_THRESHOLD: "1.05"
```

### Secrets (k8s/secrets.yaml):
```yaml
DATABASE_URL: postgresql://stryktips:StryktipsSecure2025!@postgres-service:5432/stryktips
BET365_API_KEY: ""  # Lägg till när du har API-nycklar
UNIBET_API_KEY: ""
BETSSON_API_KEY: ""
```

För att uppdatera konfiguration:
```bash
# Redigera ConfigMap eller Secrets
sudo k3s kubectl edit configmap stryktips-config -n stryktips
# eller
sudo k3s kubectl edit secret stryktips-secrets -n stryktips

# Starta om pods för att ladda ny config
sudo k3s kubectl rollout restart deployment/stryktips-app -n stryktips
```

## Backup och Restore

### Backup PostgreSQL data:
```bash
sudo k3s kubectl exec -n stryktips deployment/postgres -- pg_dump -U stryktips stryktips > backup.sql
```

### Restore PostgreSQL data:
```bash
cat backup.sql | sudo k3s kubectl exec -n stryktips -i deployment/postgres -- psql -U stryktips stryktips
```

## Nästa Steg

1. **Testa riktig data** - Ikväll ca 20:00 när Stryktipset öppnar
2. **Verifiera CronJob** - Nästa söndag 20:00
3. **Implementera riktiga odds-scrapers** - Se `docs/SCRAPING_GUIDE.md`
4. **Implementera expert-scrapers** - Aftonbladet, Expressen, SVT Sport
5. **Förbättra värdeberäkning** - Med historisk data

## Resurser

- **Dokumentation**: `/docs/` mappen
- **API Status**: `/docs/REAL_SCRAPING_STATUS.md`
- **Scraping Guide**: `/docs/SCRAPING_GUIDE.md`
- **README**: `README.md`

## Support

Vid frågor eller problem:
1. Kolla loggarna först
2. Verifiera att alla pods körs
3. Testa health endpoint: `curl http://stryktips.local/health`

---

**Grattis!** Stryktips-bot körs nu i ditt k3s cluster och kommer automatiskt uppdatera kupongen varje söndag 20:00! 🎉⚽
