# 🧪 Test Sign Up et Login

## État Actuel

### ✅ Ce qui fonctionne :
```bash
# Backend : 
POST /auth/register → 200 OK ✅
POST /auth/login → 200 OK ✅ (avec bon mot de passe)
POST /auth/login → 401 Unauthorized ❌ (avec mauvais mot de passe)
```

## 🔍 Problème "Sign Up" Non Fonctionnel

### Diagnostic

Le problème n'est PAS dans le backend (il fonctionne), mais probablement :

1. **Frontend non rechargé** : Le navigateur cache l'ancienne version
2. **Erreur JavaScript** : Console du navigateur a des erreurs
3. **Problème de routes** : Le frontend appelle les mauvaises URLs

## ✅ Solution : Vérification Step by Step

### Étape 1 : Vider le Cache du Navigateur

```
Chrome/Edge :
- Ctrl+Shift+Del (Windows) ou Cmd+Shift+Del (Mac)
- Cocher "Cached images and files"
- Clear data

OU plus simple :
- F12 (Ouvrir DevTools)
- Clic droit sur le bouton reload 🔄
- "Empty Cache and Hard Reload"
```

### Étape 2 : Vérifier la Console JavaScript

1. Ouvrir http://localhost:3000/login
2. Appuyer sur F12
3. Aller dans l'onglet "Console"
4. Regarder s'il y a des erreurs rouges

**Erreurs Communes** :
- `Failed to fetch` → Backend non accessible
- `401 Unauthorized` → Mauvais mot de passe
- `Network Error` → Problème CORS ou URL

### Étape 3 : Test Manuel Sign Up

1. **Aller sur** : http://localhost:3000/register
2. **Remplir le formulaire** :
   ```
   Email: votre@email.com
   Password: password123
   Company Name: Ma Société
   ```
3. **Cliquer** "Create Account"
4. **Vérifier** :
   - Si ça redirige vers /login → ✅ Fonctionne !
   - Si ça affiche erreur → Regarder console F12

### Étape 4 : Test Manuel Login

1. **Aller sur** : http://localhost:3000/login  
2. **Utiliser les identifiants** que vous venez de créer
3. **Cliquer** "Sign in"
4. **Vérifier** :
   - Si ça redirige vers /dashboard → ✅ Fonctionne !
   - Si erreur "Incorrect email or password" → Vérifier mot de passe

## 🧪 Test Backend Direct (pour vérifier)

### Test 1 : Créer un compte via API

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nouveau@test.com",
    "password": "monpassword123",
    "company_name": "Test Company"
  }'

# Devrait retourner :
# {
#   "email": "nouveau@test.com",
#   "company_name": "Test Company",
#   ...
#   "id": 2
# }
```

### Test 2 : Se connecter via API

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nouveau@test.com",
    "password": "monpassword123"
  }'

# Devrait retourner :
# {
#   "access_token": "eyJhbGc...",
#   "token_type": "bearer"
# }
```

Si les deux commandes fonctionnent → Le backend est OK ✅

## 🐛 Problèmes Courants et Solutions

### Problème 1 : "Incorrect email or password"

**Cause** : 
- Mot de passe incorrect
- Compte n'existe pas

**Solution** :
```bash
# Vérifier quels comptes existent :
docker-compose exec postgres psql -U postgres -d b2b_requests \
  -c "SELECT email FROM users;"

# Si votre email n'est pas dans la liste, créez-le d'abord !
```

### Problème 2 : "Network Error" ou page blanche

**Cause** :
- Backend pas démarré
- Problème de CORS
- Frontend appelle mauvaise URL

**Solution** :
```bash
# Vérifier que backend tourne :
curl http://localhost:8000/health
# Devrait retourner : {"status":"healthy"}

# Redémarrer si besoin :
docker-compose restart backend frontend
```

### Problème 3 : Page reste sur le spinner

**Cause** : Le frontend est bloqué sur la page d'authentification

**Solution** :
1. Vider le cache navigateur (Ctrl+Shift+Del)
2. Fermer TOUTES les fenêtres du navigateur
3. Rouvrir http://localhost:3000/login

### Problème 4 : OAuth Google/Microsoft ne marche pas

**Cause** : Configuration Google Cloud Console pas terminée

**Solution** : Voir `GUIDE_GOOGLE_CONSOLE.md`

## ✅ Checklist de Vérification

Après avoir suivi ce guide :

- [ ] Backend accessible : `curl http://localhost:8000/health`
- [ ] Frontend accessible : Ouvrir http://localhost:3000
- [ ] Console JavaScript sans erreurs (F12)
- [ ] Peut créer un compte sur /register
- [ ] Peut se connecter sur /login
- [ ] Redirigé vers /dashboard après login

Si TOUS ces points sont ✅, alors tout fonctionne !

## 🎯 Résultat Attendu

Après configuration :

1. **Créer un compte** :
   - /register → Remplir formulaire → "Create Account"
   - → Redirigé vers /login avec message succès

2. **Se connecter** :
   - /login → Email + Password → "Sign in"
   - → Redirigé vers /dashboard

3. **Dashboard accessible** :
   - Voir vos demandes
   - Gérer clients
   - Tout fonctionne !

---

## 💡 Note Importante

Si vous avez essayé de vous connecter AVANT de configurer Google OAuth et que ça a échoué :

**Ce n'est PAS un bug** ! C'est normal que Google OAuth ne marche pas encore.

**Pour l'instant, utilisez** :
- ✅ Email/Password (fonctionne déjà)

**Après config Google** :
- ✅ Google OAuth (fonctionnera aussi)

---

## 🆘 Toujours Bloqué ?

Envoyez-moi :

1. **Screenshot de la console** (F12 → Console)
2. **Screenshot de la page /login**
3. **Résultat de cette commande** :
   ```bash
   docker-compose logs backend | tail -20
   ```

Et je vous aiderai à débugger ! 🚀
