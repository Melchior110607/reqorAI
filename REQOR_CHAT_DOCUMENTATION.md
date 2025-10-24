# 🤖 Reqor Chat - Documentation Complète

## Vue d'ensemble

Reqor Chat est un assistant IA conversationnel qui permet de créer des requêtes (incoming/outgoing) en langage naturel. L'IA pose des questions de clarification pour obtenir toutes les informations nécessaires avant de créer la requête.

## Architecture

### Backend (`/backend/app/api/requests.py`)

#### Endpoint principal : `POST /requests/ai-chat`

**Fonctionnement :**
1. Reçoit un message utilisateur + historique de conversation
2. L'IA (GPT-4o-mini) analyse le message et extrait les informations
3. Si des infos manquent, l'IA pose une question de clarification
4. Quand tout est complet, l'IA retourne un JSON avec `action: "create_request"`
5. Le backend crée automatiquement la requête dans la base de données

**Body de la requête :**
```json
{
  "message": "Je dois demander les documents comptables à Jean Dupont",
  "conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "extracted_data": {}
}
```

**Réponses possibles :**

1. **Conversation en cours** (infos manquantes) :
```json
{
  "type": "conversation",
  "message": "Pour quel client est-ce ?",
  "ready": false
}
```

2. **Requête créée** (tout est complet) :
```json
{
  "type": "request_created",
  "message": "✅ Parfait ! J'ai créé la requête...",
  "request_id": 123,
  "ready": true
}
```

#### Logique agentique

L'IA extrait automatiquement :
- **title** : Titre court
- **description** : Description détaillée
- **type** : "incoming" ou "outgoing"
- **priority** : "low", "medium", "high", "urgent"
- **client_id** : Match avec les clients existants
- **due_date** : Convertit langage naturel en ISO format
- **email_recipients** : Pour outgoing requests

**Gestion des clients manquants :**
- L'IA compare avec la liste des clients existants
- Si non trouvé, demande confirmation ou création

**Dates en langage naturel :**
- "demain" → 2025-10-25
- "vendredi prochain" → 2025-10-31
- "dans 3 jours" → 2025-10-27

### Frontend (`/frontend/src/app/reqor-chat/page.tsx`)

#### Interface de chat

**Composants utilisés :**
- `TextType` : Animation de typing pour les réponses de l'IA
- Messages utilisateur : Bulles bleues/violettes à droite
- Messages assistant : Bulles blanches à gauche avec icône Sparkles

**Features :**
- ✅ Animation typing effet machine à écrire
- ✅ Auto-scroll vers le dernier message
- ✅ Textarea auto-resize
- ✅ Loading state ("Reqor réfléchit...")
- ✅ Success state avec redirection automatique
- ✅ Timestamps sur chaque message
- ✅ Support Enter pour envoyer (Shift+Enter pour nouvelle ligne)

**États React :**
```typescript
messages: Message[]                    // Tous les messages du chat
conversationHistory: any[]             // Format OpenAI pour l'API
extractedData: {}                      // Données extraites (inutilisé pour l'instant)
isLoading: boolean                     // État de chargement
requestCreated: boolean                // Requête créée avec succès
currentTypingIndex: number | null      // Index du message en cours de typing
```

#### Design

**Header :**
- Gradient bleu-violet
- Icône Sparkles en backdrop blur
- Titre "Chat avec Reqor"

**Zone de messages :**
- Background gris clair
- Messages animés (fade-in)
- Scroll automatique

**Input :**
- Textarea avec auto-resize
- Bouton gradient avec icône Send
- Tooltip avec astuce

### Navigation (`/frontend/src/components/layout/Sidebar.tsx`)

Le lien "✨ Chat avec Reqor" est affiché en 2ème position avec un style spécial :
- Gradient bleu-violet quand actif
- Gradient léger bleu-violet quand inactif
- Icône MessageCircle

## Flow utilisateur complet

### Exemple de conversation

**User :** "Je dois demander les documents comptables à Jean Dupont"

**Reqor :** "D'accord ! Pour quelle date avez-vous besoin de ces documents ?"

**User :** "Vendredi prochain"

**Reqor :** "Parfait ! S'agit-il d'une requête incoming (reçue du client) ou outgoing (envoyée au client) ?"

**User :** "outgoing"

**Reqor :** "Quelle priorité souhaitez-vous donner à cette requête ? (low, medium, high, urgent)"

**User :** "high"

**Reqor (JSON response) :** 
```json
{
  "action": "create_request",
  "ready": true,
  "data": {
    "title": "Demande documents comptables - Jean Dupont",
    "description": "Demander les documents comptables",
    "type": "outgoing",
    "priority": "high",
    "client_id": 42,
    "due_date": "2025-10-31"
  }
}
```

**Backend :** Crée la requête automatiquement

**Reqor (message final) :** "✅ Parfait ! J'ai créé la requête 'Demande documents comptables - Jean Dupont' (ID: 123)"

**Frontend :** Redirige vers `/request/123` après 3 secondes

## Configuration technique

### Backend

**Modèle IA :** GPT-4o-mini
- Temperature: 0.7 (conversationnel)
- Max tokens: 1000
- Prompt en français pour meilleure UX

**Base de données :**
- Table `requests` : Toutes les requêtes
- Table `clients` : Clients disponibles

**Dépendances :**
- `openai` : Client OpenAI
- `fastapi` : API REST
- `sqlalchemy` : ORM

### Frontend

**Frameworks :**
- Next.js 14+ (App Router)
- React 18+
- TypeScript
- TailwindCSS

**Librairies UI :**
- `lucide-react` : Icônes
- `TextType` : Animation typing custom

## Tests recommandés

### Test 1 : Création basique
```
User: "Créer une requête incoming pour client ABC, urgent, deadline demain"
Expected: L'IA crée directement sans poser de questions
```

### Test 2 : Clarification client
```
User: "Je dois demander des infos"
Expected: L'IA demande "Pour quel client ?"
```

### Test 3 : Client inexistant
```
User: "Requête pour client XYZ qui n'existe pas"
Expected: L'IA indique que le client n'existe pas et propose alternatives
```

### Test 4 : Date naturelle
```
User: "Deadline dans 3 jours"
Expected: L'IA convertit en date ISO correcte
```

### Test 5 : Conversation longue
```
User envoie 5+ messages avec clarifications progressives
Expected: L'IA maintient le contexte et crée la requête au final
```

## Améliorations futures

### Court terme
- [ ] Extraction intelligente du contexte (ne redemander que ce qui manque vraiment)
- [ ] Support de création de nouveau client dans le chat
- [ ] Prévisualisation de la requête avant création
- [ ] Annulation/modification avant validation finale

### Moyen terme
- [ ] Multi-requêtes en une conversation
- [ ] Support des attachments via upload
- [ ] Suggestions intelligentes basées sur l'historique
- [ ] Recherche de requêtes similaires existantes

### Long terme
- [ ] Voice input (speech-to-text)
- [ ] Intégration avec emails pour auto-création
- [ ] Templates de requêtes fréquentes
- [ ] Analytics sur les conversations

## Dépannage

### Problème : "Client non trouvé"
**Solution :** S'assurer que le client existe dans `/clients` avant de créer la requête

### Problème : Date mal parsée
**Solution :** Utiliser format explicite "YYYY-MM-DD" ou langage naturel clair

### Problème : L'IA boucle sans créer
**Solution :** Vérifier le prompt système et s'assurer que tous les champs obligatoires sont dans le JSON final

### Problème : Animation typing ne s'affiche pas
**Solution :** Vérifier que `isTyping: true` est bien défini et que `finishTyping()` est appelé

## Performance

**Temps de réponse moyen :** 1-3 secondes (selon OpenAI)
**Coût par conversation :** ~$0.001-0.005 (GPT-4o-mini)
**Limite de messages :** Aucune (historique complet envoyé)

## Sécurité

- ✅ Authentification JWT requise
- ✅ User_id filtré par token
- ✅ Validation des données avant DB insert
- ✅ Rate limiting recommandé (non implémenté)

## Contact & Support

Pour toute question : voir `README.md` principal du projet

