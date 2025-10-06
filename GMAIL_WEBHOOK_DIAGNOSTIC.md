# 🔍 Diagnostic Gmail Webhook - Pourquoi les emails n'arrivent pas

## Problème identifié

❌ **Le webhook Gmail n'est PAS implémenté** - Le code existe mais ne fait rien (ligne 269 `# TODO`)

## Checklist de diagnostic

### 1. Gmail API activée ?

**Vérifier dans Google Cloud Console** :
- https://console.cloud.google.com/apis/library/gmail.googleapis.com
- Le projet : `475859287473`
- ✅ API doit être **ENABLED**

### 2. Webhook Push Notifications configuré ?

Gmail utilise **Pub/Sub** pour les webhooks, pas des webhooks HTTP directs !

**Étapes pour Gmail** :
1. Créer un Topic Pub/Sub
2. Configurer Gmail Watch
3. Recevoir les notifications
4. Récupérer les emails via Gmail API

⚠️ **C'EST COMPLEXE** - Gmail ne fait pas de webhooks simples !

### 3. Solution alternative : Polling

Au lieu d'attendre un webhook, on peut **poller Gmail** régulièrement :

```python
# Toutes les 30 secondes, checker les nouveaux emails
scheduler.add_job(
    func=fetch_gmail_emails,
    trigger='interval',
    seconds=30
)
```

## 🎯 Solution recommandée pour le debug

**OPTION SIMPLE pour tester MAINTENANT** :

1. **Bouton manuel "Sync Gmail"** dans l'interface
2. Quand tu cliques, ça va chercher les emails
3. Tu vois immédiatement si ça marche

### Implémenter le sync manuel

**Backend** : Endpoint pour synchroniser manuellement
```python
POST /email/sync-gmail
→ Va chercher les N derniers emails Gmail
→ Les stock dans intercepted_emails
```

**Frontend** : Bouton "Synchroniser Gmail" dans la page debug
```typescript
<Button onClick={syncGmail}>
  Sync Gmail
</Button>
```

## Recommandation

1. **Maintenant** : Implémenter le sync manuel pour tester
2. **Plus tard** : Implémenter le vrai webhook Pub/Sub

Veux-tu que j'implémente le sync manuel pour qu'on puisse tester immédiatement ?

