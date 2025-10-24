# ✨ Reqor Chat - Assistant IA Conversationnel

## Description

Interface de chat élégante permettant de créer des requêtes (incoming/outgoing) en **langage naturel**. L'IA **Reqor** pose des questions de clarification de manière agentique jusqu'à avoir toutes les informations nécessaires.

## Features

- 🤖 **IA conversationnelle** - Dialogue naturel avec l'assistant
- 💬 **Questions de clarification** - L'IA demande les infos manquantes une par une
- 📅 **Dates en langage naturel** - "demain", "vendredi prochain", "dans 3 jours"
- 👥 **Match automatique des clients** - Recherche dans la base de données existante
- ⚡ **Création automatique** - Requête créée dès que toutes les infos sont disponibles
- ✨ **Animation typing** - Effet machine à écrire pour les réponses de l'IA
- 🎨 **UI magnifique** - Design moderne avec gradients et animations

## Usage

1. **Accéder au chat** : `/reqor-chat` ou cliquer sur "✨ Chat avec Reqor" dans le sidebar
2. **Décrire votre requête** : En langage naturel, ex: "Je dois demander les documents à Jean"
3. **Répondre aux questions** : Reqor pose des questions pour compléter les infos
4. **Validation automatique** : Dès que tout est complet, la requête est créée
5. **Redirection** : Vers la page de la requête créée

## Exemple de conversation

```
User: Je dois demander des documents à Jean Dupont

Reqor: D'accord ! Pour quelle date avez-vous besoin de ces documents ?

User: Vendredi prochain

Reqor: Parfait ! S'agit-il d'une requête incoming ou outgoing ?

User: outgoing

Reqor: Quelle priorité ? (low/medium/high/urgent)

User: high

Reqor: ✅ Parfait ! J'ai créé la requête "Demande documents - Jean Dupont" (ID: 123)
[Redirection vers /request/123]
```

## Technologies

- **Frontend** : Next.js 14, React, TypeScript, TailwindCSS
- **Backend** : FastAPI, OpenAI GPT-4o-mini
- **UI Components** : TextType (animation typing), Lucide Icons
- **Style** : Gradient bleu-violet, animations CSS

## Architecture

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         v
┌─────────────────┐      ┌──────────────────┐
│  Frontend Chat  │─────>│ Backend Endpoint │
│   (page.tsx)    │<─────│  /ai-chat        │
└─────────────────┘      └────────┬─────────┘
         │                         │
         v                         v
┌─────────────────┐      ┌──────────────────┐
│  TextType       │      │   OpenAI API     │
│  Animation      │      │   (GPT-4o-mini)  │
└─────────────────┘      └────────┬─────────┘
                                   │
                                   v
                         ┌──────────────────┐
                         │ Request Created  │
                         │   in Database    │
                         └──────────────────┘
```

## Fichiers principaux

- `page.tsx` - Composant principal du chat
- `../../../backend/app/api/requests.py` - Endpoint `/ai-chat`
- `../../components/ui/TextType.tsx` - Animation typing
- `../../components/layout/Sidebar.tsx` - Navigation

## Configuration

Aucune configuration nécessaire ! Le chat utilise :
- Token JWT du localStorage
- Endpoint backend : `http://localhost:8000`
- OpenAI API key (configurée dans le backend)

## Développement

### Structure des états

```typescript
messages: Message[]              // Historique du chat
conversationHistory: any[]       // Format OpenAI
isLoading: boolean              // État de chargement
requestCreated: boolean         // Succès final
currentTypingIndex: number      // Animation en cours
```

### Flux de données

1. User tape un message
2. Frontend → POST `/requests/ai-chat` avec message + historique
3. Backend → OpenAI API pour analyse
4. OpenAI → Répond avec question OU JSON de création
5. Si JSON → Backend crée la requête dans DB
6. Frontend affiche réponse avec animation
7. Si créée → Redirection automatique

## Personnalisation

### Modifier le comportement de l'IA

Éditer le system prompt dans `backend/app/api/requests.py` :
```python
system_prompt = f"""Tu es Reqor, un assistant IA...
[Modifier ici les instructions]
"""
```

### Changer le style de l'UI

Éditer `page.tsx` :
```typescript
// Couleurs du gradient
className="bg-gradient-to-r from-blue-500 to-purple-600"

// Animation typing speed
<TextType typingSpeed={20} />
```

### Ajouter des champs

1. Ajouter dans le system prompt (backend)
2. Mettre à jour l'interface `Message` (frontend)
3. Gérer dans la création de Request

## Limitations actuelles

- Pas de création de nouveau client dans le chat (doit exister au préalable)
- Pas de support des attachments
- Une seule requête par conversation
- Pas de modification après création

## Améliorations prévues

- [ ] Création de client dans le chat
- [ ] Multi-requêtes en une conversation
- [ ] Prévisualisation avant validation
- [ ] Support des attachments
- [ ] Voice input

## Documentation complète

Voir `REQOR_CHAT_DOCUMENTATION.md` à la racine du projet

## Tests

Guide de test complet : `REQOR_CHAT_TEST_GUIDE.md`

## License

Même licence que le projet principal reqorAI

