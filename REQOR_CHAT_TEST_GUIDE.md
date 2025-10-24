# 🧪 Guide de test Reqor Chat

## Prérequis

1. **Backend en cours d'exécution**
   ```bash
   cd backend
   docker-compose up
   # OU
   uvicorn app.main:app --reload
   ```

2. **Frontend en cours d'exécution**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Base de données avec des clients**
   - Au moins un client doit exister dans la DB
   - Pour créer un client : aller sur `/clients` et ajouter un client test

## Test 1 : Conversation basique (complète)

### Étape 1 : Ouvrir le chat
1. Naviguer vers `http://localhost:3000/reqor-chat`
2. Vous devriez voir le message d'accueil de Reqor avec animation typing

### Étape 2 : Envoyer un message complet
**Message :** 
```
Je dois envoyer une demande urgente à Jean Dupont pour lui demander les documents comptables avant vendredi prochain
```

**Résultat attendu :**
- Reqor pose des questions pour les infos manquantes (type, priorité, etc.)
- OU si toutes les infos sont claires, Reqor crée directement la requête

### Étape 3 : Répondre aux questions
Si Reqor demande des clarifications, répondez :
- Type : "outgoing"
- Priorité : "high"
- Client : "Jean Dupont" (doit exister dans votre DB)

### Étape 4 : Validation
Une fois toutes les infos fournies :
- Message de succès : "✅ Parfait ! J'ai créé la requête..."
- Redirection automatique vers la page de la requête après 3 secondes
- Vérifier que la requête apparaît dans `/outgoing-requests`

---

## Test 2 : Clarification progressive

### Message initial incomplet
```
Je dois créer une requête
```

**Comportement attendu :**
1. Reqor : "Pour quel client est-ce ?"
2. User : "Acme Corp"
3. Reqor : "S'agit-il d'une requête incoming ou outgoing ?"
4. User : "incoming"
5. Reqor : "Quelle est la date d'échéance ?"
6. User : "demain"
7. Reqor : "Quelle priorité ? (low/medium/high/urgent)"
8. User : "medium"
9. Reqor : "De quoi s'agit-il exactement ?"
10. User : "Demande de support technique"
11. Reqor : Crée la requête ✅

---

## Test 3 : Client inexistant

### Message
```
Créer une requête pour ClientFantome123
```

**Résultat attendu :**
- Reqor indique que ce client n'existe pas
- Propose de vérifier l'orthographe
- Ou propose de créer un nouveau client (si implémenté)

---

## Test 4 : Dates en langage naturel

Tester différents formats :

| Message | Date attendue |
|---------|--------------|
| "deadline demain" | 2025-10-25 |
| "pour vendredi" | 2025-10-31 (prochain vendredi) |
| "dans 3 jours" | 2025-10-27 |
| "pour le 2025-11-15" | 2025-11-15 |

---

## Test 5 : UI et animations

### Vérifications visuelles

1. **Header**
   - ✅ Gradient bleu-violet
   - ✅ Icône Sparkles en backdrop blur
   - ✅ Titre et sous-titre visibles

2. **Messages utilisateur**
   - ✅ Bulles bleues-violettes à droite
   - ✅ Texte blanc lisible
   - ✅ Timestamp visible

3. **Messages Reqor**
   - ✅ Bulles blanches à gauche
   - ✅ Badge "Reqor" avec icône Sparkles
   - ✅ Animation typing (effet machine à écrire)
   - ✅ Texte gris foncé lisible

4. **Input**
   - ✅ Textarea auto-resize
   - ✅ Bouton avec gradient et icône Send
   - ✅ Disabled pendant chargement
   - ✅ Enter pour envoyer (Shift+Enter = nouvelle ligne)

5. **Loading state**
   - ✅ Bulle avec "Reqor réfléchit..." et spinner
   - ✅ Bouton et textarea désactivés

6. **Success state**
   - ✅ Bannière verte avec ✅
   - ✅ "Requête créée avec succès ! Redirection..."
   - ✅ Redirection après ~3 secondes

---

## Test 6 : Navigation

1. **Sidebar**
   - ✅ Lien "✨ Chat avec Reqor" visible en 2ème position
   - ✅ Style spécial gradient bleu-violet
   - ✅ Actif quand sur `/reqor-chat`

2. **Depuis le dashboard**
   - Cliquer sur "✨ Chat avec Reqor" dans le sidebar
   - Devrait naviguer vers le chat

---

## Test 7 : Erreurs et edge cases

### Test 7.1 : Message vide
- Essayer d'envoyer un message vide
- Bouton devrait être désactivé

### Test 7.2 : Timeout API
- Simuler un timeout (backend down)
- Message d'erreur devrait s'afficher

### Test 7.3 : Token expiré
- Expirer le token JWT
- Devrait rediriger vers `/login`

### Test 7.4 : Conversation très longue
- Envoyer 10+ messages
- Historique devrait être maintenu
- Scroll devrait suivre automatiquement

---

## Checklist finale ✅

Avant de considérer le test complet :

### Backend
- [ ] Endpoint `/requests/ai-chat` répond correctement
- [ ] Clients sont chargés depuis la DB
- [ ] Dates naturelles sont parsées correctement
- [ ] Requête est créée dans la DB avec tous les champs
- [ ] Erreurs sont gérées gracieusement

### Frontend
- [ ] Page `/reqor-chat` s'affiche correctement
- [ ] Animation typing fonctionne
- [ ] Messages s'affichent dans l'ordre
- [ ] Auto-scroll vers le bas
- [ ] Loading state visible
- [ ] Success avec redirection
- [ ] Lien dans sidebar fonctionne

### UX
- [ ] Reqor pose des questions naturelles
- [ ] Une question à la fois (pas overload)
- [ ] Langage amical et professionnel
- [ ] Confirmation claire quand requête créée
- [ ] UI responsive et élégante

---

## Debugging

### Console Browser (F12)

Vérifier les logs :
```javascript
// Requête envoyée
POST http://localhost:8000/requests/ai-chat
Body: {"message": "...", "conversation_history": [...]}

// Réponse reçue
Response: {"type": "conversation", "message": "...", "ready": false}
// OU
Response: {"type": "request_created", "message": "...", "request_id": 123, "ready": true}
```

### Backend logs

```bash
# Voir les logs FastAPI
docker-compose logs -f backend

# Ou si mode dev
uvicorn app.main:app --reload --log-level debug
```

Chercher :
- Requêtes POST `/requests/ai-chat`
- Réponses OpenAI
- Création de Request dans DB

---

## Métriques de performance

- **Temps de réponse IA :** < 3 secondes
- **Animation typing :** Fluide, pas saccadée
- **Scroll auto :** Instantané
- **Redirection :** Après 3 secondes

---

## Problèmes connus

### 1. Requête créée mais pas visible
**Solution :** Rafraîchir `/outgoing-requests` ou `/incoming-requests`

### 2. Animation typing ne se termine pas
**Solution :** Vérifier que `onSentenceComplete` est bien appelé dans TextType

### 3. Client pas trouvé alors qu'il existe
**Solution :** Vérifier l'orthographe exacte dans la DB (case-sensitive)

---

## Support

Si un test échoue, vérifier :
1. Les logs backend (erreurs API)
2. La console browser (erreurs JS)
3. La base de données (clients existants)
4. La documentation : `REQOR_CHAT_DOCUMENTATION.md`

