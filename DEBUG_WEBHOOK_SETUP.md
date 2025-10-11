# 🔧 Debug Guide - Activer les Webhooks

## ✅ Ce qui a été ajouté

1. **Endpoint debug** : `/debug/me` - Affiche vos infos + IDs de connexions
2. **Auto-setup webhooks** : Les nouveaux comptes auront les webhooks automatiquement
3. **Endpoint manuel** : `/email/webhook/setup/{connection_id}` - Pour activer manuellement

---

## 🎯 Pour ACTIVER vos webhooks existants

### Méthode 1 : Via le navigateur (plus simple)

#### Étape 1 : Allez sur l'endpoint debug

Ouvrez votre navigateur sur : **http://localhost:8000/debug/me**

Vous verrez vos informations :
```json
{
  "user": {
    "id": 1,
    "email": "your@email.com",
    "name": "Your Name"
  },
  "connections": [
    {
      "id": 1,
      "provider": "GMAIL",
      "email_address": "your@gmail.com",
      "status": "ACTIVE"
    }
  ],
  "instructions": {
    "setup_gmail_webhook": "curl -X POST http://localhost:8000/email/webhook/setup/1 -H 'Authorization: Bearer YOUR_TOKEN'",
    "note": "Replace CONNECTION_ID with the Gmail connection id above"
  }
}
```

#### Étape 2 : Notez l'ID de connexion Gmail

Dans l'exemple ci-dessus, c'est `1`.

#### Étape 3 : Récupérez votre token

**Option A** - Via les outils développeur :
1. Sur n'importe quelle page de votre app (http://localhost:3000)
2. Ouvrez les outils développeur (Clic droit > Inspecter)
3. Onglet **Application** (ou **Storage**)
4. Sidebar gauche : **Local Storage** > **http://localhost:3000**
5. Trouvez la clé `token`
6. Copiez la valeur (long texte qui commence par `eyJ...`)

**Option B** - Via la console :
1. Sur n'importe quelle page (http://localhost:3000)
2. Ouvrez les outils développeur
3. Onglet **Console**
4. Tapez : `localStorage.getItem('token')`
5. Copiez le résultat (entre guillemets)

#### Étape 4 : Activez le webhook

Dans votre terminal :

```bash
curl -X POST http://localhost:8000/email/webhook/setup/1 \
  -H "Authorization: Bearer VOTRE_TOKEN_ICI"
```

Remplacez :
- `1` par votre connection ID
- `VOTRE_TOKEN_ICI` par le token copié

---

### Méthode 2 : Via un script Python temporaire

Créez un fichier `setup_my_webhook.py` :

```python
import requests

# REMPLACEZ CES VALEURS
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Votre token
CONNECTION_ID = 1  # ID de votre connexion Gmail

# Activation du webhook
response = requests.post(
    f"http://localhost:8000/email/webhook/setup/{CONNECTION_ID}",
    headers={"Authorization": f"Bearer {TOKEN}"}
)

print("Response:", response.status_code)
print(response.json())
```

Puis exécutez :
```bash
python setup_my_webhook.py
```

---

## 🎉 Pour les NOUVEAUX comptes

Rien à faire ! Les webhooks s'activent **automatiquement** maintenant quand :
1. Un utilisateur connecte Gmail/Outlook
2. Le callback OAuth réussit
3. Le webhook est configuré en arrière-plan

---

## 🧪 TESTER que ça marche

### 1. Vérifier le webhook dans la DB

```bash
docker exec -it projectai-postgres-1 psql -U postgres -d b2b_requests
```

```sql
SELECT id, provider, status, expires_at, notification_count 
FROM webhook_subscriptions;
```

Vous devriez voir votre webhook Gmail avec `status = 'active'`.

### 2. Envoyer un email de test

Envoyez un email à votre Gmail connecté.

### 3. Surveiller les logs

**Backend** :
```bash
docker logs -f projectai-backend-1 | grep -E "(📨|📬|✅)"
```

**ngrok** (dans le terminal où ngrok tourne) :
Vous verrez `POST /webhook/gmail` apparaître

**ngrok web interface** :
Ouvrez http://127.0.0.1:4040 pour voir tous les détails

### 4. Vérifier les emails interceptés

```bash
docker exec -it projectai-postgres-1 psql -U postgres -d b2b_requests
```

```sql
SELECT id, subject, sender_email, email_received_at 
FROM intercepted_emails 
ORDER BY email_received_at DESC 
LIMIT 5;
```

---

## ❓ Troubleshooting

### "GMAIL_PUBSUB_TOPIC not configured"

Vérifiez votre `.env` :
```bash
GMAIL_PUBSUB_TOPIC="projects/bbrm-474222/topics/gmail-notifications"
GMAIL_PROJECT_ID="bbrm-474222"
OUTLOOK_TENANT_ID="3e90cbca-024c-4aa6-97b6-bcf8e9f95d15"
WEBHOOK_BASE_URL="https://VOTRE-URL-NGROK.ngrok-free.app"
```

Puis redémarrez :
```bash
docker-compose restart backend
```

### Webhook ne reçoit pas de notifications

Vérifiez :
1. ngrok est toujours en cours d'exécution
2. `WEBHOOK_BASE_URL` dans `.env` correspond à l'URL ngrok actuelle
3. La Pub/Sub subscription dans Google Cloud utilise la bonne URL ngrok
4. Le webhook est bien activé (check la DB)

---

## 🎯 Récapitulatif

**Pour vos comptes existants** :
1. ✅ Allez sur http://localhost:8000/debug/me
2. ✅ Récupérez votre token (localStorage)
3. ✅ Exécutez la commande curl avec votre connection ID
4. ✅ Testez en envoyant un email

**Pour les nouveaux comptes** :
✅ Automatique ! Rien à faire !

---

Ready to activate your webhooks? Go to http://localhost:8000/debug/me ! 🚀

