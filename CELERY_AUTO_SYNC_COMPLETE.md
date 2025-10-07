# ✅ Synchronisation Automatique avec Celery - COMPLETE

## 🎯 Objectif Atteint

**Synchronisation automatique des emails toutes les 30 minutes sans doublons**

---

## 📋 Ce qui a été implémenté

### 1. **Anti-Doublons (Triple Protection)**

✅ **Filtre par timestamp**
- Gmail : `after:YYYY/MM/DD`
- Outlook : `receivedDateTime ge YYYY-MM-DDTHH:MM:SSZ`
- Utilise `connection.last_sync` pour ne récupérer que les nouveaux

✅ **ID Unique** (`message_id`)
- Colonne `message_id VARCHAR UNIQUE` dans `intercepted_emails`
- Index pour performance
- Contrainte DB native

✅ **Vérification applicative**
- Check avant insertion
- Logs : "X nouveaux, Y doublons évités"

---

### 2. **Celery Beat (Automatisation)**

✅ **Configuration Celery**
- `/backend/app/celery_app.py` créé
- Tâche périodique configurée : `crontab(minute='*/30')` = toutes les 30min
- Queue dédiée : `email_sync`

✅ **Tâches async**
- `sync_all_user_emails()` : Sync tous les utilisateurs
- `sync_user_emails(user_id)` : Sync un utilisateur spécifique
- `sync_connection_emails(connection_id)` : Sync une connexion

✅ **Docker Services**
- `celery_worker` : Exécute les tâches
- `celery_beat` : Scheduler (déclenche toutes les 30min)

---

### 3. **Logs de Synchronisation**

✅ **Modèle BDD** (`sync_logs`)
- `sync_type` : "auto" ou "manual"
- `total_synced`, `total_duplicates`, `connections_processed`
- `details` (JSON) : Résultats par connexion
- `error` : Si échec

✅ **Endpoint API**
- `GET /email/sync-logs` : Récupère les 50 derniers logs

✅ **Page Frontend** (`/auto-sync`)
- Dashboard avec stats
- Liste des synchronisations
- Détails par connexion (expandable)
- Auto-refresh toutes les 30 secondes

---

## 🏗️ Architecture Finale

```
┌──────────────────────────────────────────────────────────────────┐
│                    CELERY BEAT (Scheduler)                       │
│             Déclenche toutes les 30 minutes                      │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│               CELERY WORKER (Exécute les tâches)                 │
│                                                                  │
│  sync_all_user_emails()                                          │
│    ├─ Récupère toutes les connexions actives                    │
│    ├─ Pour chaque connexion:                                    │
│    │   ├─ Récupère last_sync                                    │
│    │   ├─ Appelle Gmail/Outlook API avec filtre date           │
│    │   ├─ Vérifie message_id (anti-doublon)                    │
│    │   ├─ Insère les nouveaux emails                           │
│    │   └─ Met à jour last_sync = NOW()                         │
│    └─ Enregistre sync_log en DB                                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL                                  │
│                                                                  │
│  intercepted_emails   ← Emails avec message_id UNIQUE           │
│  email_connections    ← last_sync timestamp                     │
│  sync_logs            ← Historique des syncs                    │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                 FRONTEND (/auto-sync)                            │
│                                                                  │
│  - Dashboard avec stats                                          │
│  - Liste des syncs (auto/manual)                                │
│  - Détails par connexion                                        │
│  - Auto-refresh 30s                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Démarrage

### Lancer tous les services
```bash
docker-compose up -d
```

**Services démarrés :**
- `postgres` : Base de données
- `redis` : Broker Celery
- `backend` : API FastAPI
- `celery_worker` : Worker Celery
- `celery_beat` : Scheduler (syncs automatiques)
- `frontend` : Next.js

### Vérifier Celery
```bash
# Logs worker
docker logs projectai-celery_worker-1 --tail 50 -f

# Logs beat (scheduler)
docker logs projectai-celery_beat-1 --tail 50 -f
```

---

## 🧪 Test du Système

### Test 1 : Sync Manuelle (avec anti-doublon)
```bash
# 1. Sync Gmail
curl -X POST http://localhost:8000/email/sync/gmail \
  -H "Authorization: Bearer YOUR_TOKEN"

# Résultat : "20 nouveaux emails"

# 2. Re-sync immédiatement
curl -X POST http://localhost:8000/email/sync/gmail \
  -H "Authorization: Bearer YOUR_TOKEN"

# Résultat : "0 nouveaux emails (20 doublons évités)"
```

### Test 2 : Sync Automatique (attendre 30min)
1. Ouvrir http://localhost:3000/auto-sync
2. Attendre la prochaine demi-heure (14:00, 14:30, 15:00...)
3. Un nouveau log apparaîtra automatiquement
4. Vérifier les stats : nouveaux / doublons / connexions

### Test 3 : Arrêt/Redémarrage Docker
```bash
# Arrêter tous les containers
docker-compose stop

# ✅ Celery s'arrête automatiquement

# Redémarrer
docker-compose up -d

# ✅ Celery Beat reprend le schedule
# ✅ Prochaine sync à la prochaine demi-heure
```

---

## 🔧 Configuration

### Changer l'intervalle de sync

Éditer `/backend/app/celery_app.py` :

```python
celery_app.conf.beat_schedule = {
    'sync-all-emails-every-30min': {
        'task': 'app.tasks.email_sync.sync_all_user_emails',
        'schedule': crontab(minute='*/15'),  # ← Changer à 15min
        'options': {'queue': 'email_sync'}
    },
}
```

Puis redémarrer :
```bash
docker-compose restart celery_beat celery_worker
```

### Désactiver temporairement

```bash
# Arrêter Celery Beat seulement
docker-compose stop celery_beat

# Les syncs manuelles fonctionnent toujours
# Les syncs automatiques sont suspendues
```

---

## 📊 Monitoring

### Voir les logs en temps réel
```bash
# Toutes les tâches Celery
docker logs projectai-celery_worker-1 -f

# Scheduler Beat
docker logs projectai-celery_beat-1 -f

# Backend FastAPI
docker logs projectai-backend-1 -f
```

### Interface Web
- **Frontend** : http://localhost:3000/auto-sync
- **API Logs** : http://localhost:8000/email/sync-logs

---

## ❓ FAQ

### Q: Comment savoir si Celery fonctionne ?
```bash
docker logs projectai-celery_beat-1 --tail 5
# Doit afficher : "beat: Starting..."
```

### Q: La sync automatique ne se déclenche pas ?
1. Vérifier que Celery Beat tourne : `docker ps | grep celery_beat`
2. Vérifier les logs : `docker logs projectai-celery_beat-1`
3. Attendre la prochaine demi-heure (14:00, 14:30, 15:00, etc.)

### Q: Comment forcer une sync maintenant (sans attendre 30min) ?
Option 1 : Bouton manual dans `/ai-monitoring`
Option 2 : API `POST /email/sync/gmail`
Option 3 : Appeler la tâche manuellement :
```bash
docker exec projectai-celery_worker-1 \
  celery -A app.celery_app call app.tasks.email_sync.sync_all_user_emails
```

### Q: Que se passe-t-il en production ?
- Celery Beat tourne 24/7
- Sync automatique toutes les 30min
- Si Docker redémarre → Celery reprend automatiquement
- Logs enregistrés en DB pour monitoring

### Q: Comment voir les emails qui ont été ignorés (doublons) ?
- Page `/auto-sync` → Cliquez sur "Détails"
- Voir `X doublons évités` pour chaque sync
- Vérifier les logs Celery Worker pour les prints "🔄 Email XXX déjà traité"

---

## 📁 Fichiers Créés/Modifiés

### Backend
- ✅ `/backend/app/celery_app.py` - Configuration Celery
- ✅ `/backend/app/tasks/__init__.py` - Module tasks
- ✅ `/backend/app/tasks/email_sync.py` - Tâches asynchrones
- ✅ `/backend/app/models/sync_log.py` - Modèle logs
- ✅ `/backend/app/models/intercepted_email.py` - Ajout `message_id UNIQUE`
- ✅ `/backend/app/services/gmail_service.py` - Filtre `since_timestamp`
- ✅ `/backend/app/services/outlook_service.py` - Filtre `since_timestamp`
- ✅ `/backend/app/services/email_service.py` - Anti-doublon par `message_id`
- ✅ `/backend/app/api/email.py` - Endpoint `/sync-logs`, tracking `last_sync`

### Frontend
- ✅ `/frontend/src/app/auto-sync/page.tsx` - Page monitoring
- ✅ `/frontend/src/components/layout/Sidebar.tsx` - Lien "Auto Sync"

### Infrastructure
- ✅ `/docker-compose.yml` - Services `celery_worker` et `celery_beat`
- ✅ `/ANTI_DOUBLON_SOLUTION.md` - Documentation anti-doublons
- ✅ `/CELERY_AUTO_SYNC_COMPLETE.md` - Ce document

---

## ✅ Checklist Finale

- [x] Anti-doublons par timestamp (last_sync)
- [x] Anti-doublons par message_id unique
- [x] Vérification applicative avant insertion
- [x] Celery configuré avec Redis
- [x] Celery Beat pour tâches périodiques (30min)
- [x] Docker services celery_worker et celery_beat
- [x] Modèle sync_logs pour historique
- [x] Endpoint API /sync-logs
- [x] Page frontend /auto-sync avec dashboard
- [x] Auto-refresh frontend (30s)
- [x] Navigation sidebar avec lien
- [x] Tests manuels : sync, doublons, redémarrage
- [x] Documentation complète

---

## 🎉 Résultat Final

**Système complet de synchronisation automatique avec :**
- ✅ **Zéro doublon** garanti
- ✅ **Sync toutes les 30min** automatique
- ✅ **Monitoring en temps réel** via interface web
- ✅ **Performance optimisée** (filtre par date)
- ✅ **Arrêt/Redémarrage propre** avec Docker
- ✅ **Logs détaillés** pour debug
- ✅ **Production-ready** 🚀

**Pages créées :**
1. `/ai-monitoring` - Debug emails bruts
2. `/client-matching` - Test algorithme matching
3. `/auto-sync` - Monitoring synchronisations automatiques

**Prochaine étape : Classification IA avec GPT-4 ! 🤖**

