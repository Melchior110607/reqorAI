# 🐛 Mode DEBUG : Synchronisation Toutes les Minutes

## ⚙️ Configuration Actuelle

### ⏱️ Intervalle : **1 minute** (au lieu de 30min)
### 📊 Limite : **10 emails max** par sync (au lieu de 50)

---

## 🎯 Optimisations Appliquées

### 1. **Fréquence augmentée mais volume réduit**
- **Avant** : 50 emails toutes les 30min = ~100 emails/heure
- **Maintenant** : 10 emails chaque minute = **600 emails/heure max**
- ✅ Plus réactif pour le debug
- ✅ Charge distribuée sur plusieurs petites syncs

### 2. **Protection Anti-Doublons Renforcée**
- ✅ Filtre par `last_sync` (ne récupère que les nouveaux)
- ✅ Vérification par `message_id` unique en DB
- ✅ Check applicatif avant insertion
- 🛡️ **Impossible d'avoir des doublons même à 1min d'intervalle**

### 3. **Skip si Aucune Connexion**
- Si aucune connexion email active → Skip immédiat
- Évite les appels inutiles à la DB/API

---

## 📈 Impact Performance

### Charge CPU/Mémoire
- **Celery Worker** : Traite max 10 emails/min
- **PostgreSQL** : 1 requête SELECT + X INSERT (X ≤ 10)
- **APIs externes** : 1 appel Gmail/Outlook par minute
- 💡 **Impact minimal** : Les APIs ont des rate limits de milliers de requêtes/jour

### Charge Réseau
- Gmail API : ~1-2 requêtes/min
- Outlook Graph : ~1-2 requêtes/min
- ✅ **Bien en dessous des limites** (10,000+ requêtes/jour autorisées)

---

## 🧪 Test Rapide

### 1. Vérifier que Celery tourne
```bash
docker logs projectai-celery_beat-1 --tail 10 -f
```

Tu devrais voir quelque chose comme :
```
[2025-10-07 22:30:00] Executing task: sync_all_user_emails
[2025-10-07 22:31:00] Executing task: sync_all_user_emails
[2025-10-07 22:32:00] Executing task: sync_all_user_emails
```

### 2. Voir les résultats
```bash
# Option 1 : Frontend
# Ouvrir http://localhost:3000/auto-sync
# → Les logs apparaissent toutes les minutes

# Option 2 : API directe
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/email/sync-logs
```

### 3. Vérifier les doublons
```bash
# Voir si des emails sont bien évités
docker logs projectai-celery_worker-1 | grep "🔄"
# Doit afficher : "🔄 Email XXX déjà traité, ignoré"
```

---

## 🔄 Revenir en Mode Production (30min)

### Option 1 : Modifier le code
Éditer `/backend/app/celery_app.py` :
```python
'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes
```

### Option 2 : Variable d'environnement (plus flexible)
Éditer `/backend/app/celery_app.py` :
```python
from app.database.config import settings

# Ajouter dans settings
sync_interval = int(os.getenv('SYNC_INTERVAL_MIN', '30'))

celery_app.conf.beat_schedule = {
    'sync-emails': {
        'task': 'app.tasks.email_sync.sync_all_user_emails',
        'schedule': crontab(minute=f'*/{sync_interval}'),
        'options': {'queue': 'email_sync'}
    },
}
```

Puis dans `.env` :
```bash
SYNC_INTERVAL_MIN=30  # Production
# ou
SYNC_INTERVAL_MIN=1   # Debug
```

### Redémarrer
```bash
docker-compose restart celery_beat celery_worker
```

---

## ⚠️ Contraintes & Limites

### Gmail API
- **Quota** : 1 milliard de requêtes/jour (gratuit)
- **Rate limit** : 250 requêtes/seconde
- ✅ 1 requête/minute = **0.017 req/sec** → Aucun souci

### Outlook Graph API
- **Quota** : 10,000 requêtes/10min
- **Rate limit** : ~1,000 req/min
- ✅ 1 requête/minute → Aucun souci

### PostgreSQL
- **Insertions** : Max 10 emails/min × 60min = **600 rows/heure**
- **Taille DB** : Avec 100 caractères/email = ~60KB/heure
- ✅ Négligeable même sur plusieurs jours de debug

### Redis (Celery Broker)
- **Messages** : 1 tâche/min = 1,440 messages/jour
- **Mémoire** : Quelques KB par message
- ✅ Redis peut gérer des millions de messages

---

## 📊 Monitoring en Temps Réel

### Frontend
```
http://localhost:3000/auto-sync
```
- Stats mises à jour automatiquement
- Auto-refresh toutes les 30 secondes
- Voir nouveaux emails vs doublons évités

### Logs Celery
```bash
# Worker (exécute les tâches)
docker logs projectai-celery_worker-1 -f

# Beat (déclenche les syncs)
docker logs projectai-celery_beat-1 -f
```

### Base de Données
```bash
# Compter les emails
docker exec projectai-postgres-1 psql -U postgres -d b2b_requests \
  -c "SELECT COUNT(*) FROM intercepted_emails;"

# Compter les syncs
docker exec projectai-postgres-1 psql -U postgres -d b2b_requests \
  -c "SELECT COUNT(*), sync_type FROM sync_logs GROUP BY sync_type;"
```

---

## 💡 Recommandations

### Pour le Debug (Maintenant)
- ✅ **1 minute** : Parfait pour voir les changements rapidement
- ✅ **10 emails** : Réduit la charge, évite le spam
- ✅ Garder pendant les tests

### Pour la Production
- 🔧 **30 minutes** : Balance entre réactivité et charge
- 🔧 **50 emails** : Capacité suffisante pour gros volumes
- 🔧 Changer quand tout fonctionne bien

### Si Grosse Charge Attendue
- Option 1 : **15 minutes** + **20 emails** (middle ground)
- Option 2 : **5 minutes** + **10 emails** (très réactif)
- Option 3 : Webhook temps réel (Phase future)

---

## 🚀 Commandes Utiles

```bash
# Démarrer les services
docker-compose up -d

# Voir les logs en direct
docker-compose logs -f celery_worker celery_beat

# Redémarrer Celery uniquement
docker-compose restart celery_beat celery_worker

# Arrêter temporairement les syncs auto
docker-compose stop celery_beat

# Tester une sync manuelle
curl -X POST http://localhost:8000/email/sync/gmail \
  -H "Authorization: Bearer YOUR_TOKEN"

# Vérifier l'état des containers
docker-compose ps
```

---

## ✅ Checklist de Vérification

Après avoir redémarré Celery avec la config 1min :

- [ ] Celery Beat démarre sans erreur
- [ ] Première sync se déclenche à la minute suivante
- [ ] Log apparaît dans `/auto-sync` après 1 minute
- [ ] Pas de doublons (vérifier "X doublons évités")
- [ ] CPU/Mémoire stables (via `docker stats`)
- [ ] Aucune erreur dans les logs

**Si tout est ✅ → Le mode debug 1min fonctionne parfaitement !**

---

## 🔙 Résumé

| Paramètre | Avant (Prod) | Maintenant (Debug) |
|-----------|--------------|-------------------|
| **Intervalle** | 30 minutes | 1 minute |
| **Emails/sync** | 50 | 10 |
| **Réactivité** | Normale | Très rapide ⚡ |
| **Charge** | Moyenne | Optimisée 🎯 |
| **Doublons** | Évités ✅ | Évités ✅ |

**Parfait pour le debug, facile à repasser en prod ! 🚀**

