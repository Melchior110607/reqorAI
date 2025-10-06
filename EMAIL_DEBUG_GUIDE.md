# 🔍 Guide de Debug - Email Pattern Matching

## Vue d'ensemble

Cette interface de debug permet de tester et valider l'algorithme de reconnaissance client basé sur les emails interceptés.

## Accès

🔗 **URL**: http://localhost:3000/ai-monitoring

⚠️ **Note**: Cette page sera supprimée en production - elle est uniquement pour le développement.

## Fonctionnalités

### 1. Statistiques en temps réel
- **Total Emails**: Nombre total d'emails interceptés
- **Matched**: Emails associés à un client
- **Unmatched**: Emails sans correspondance client
- **Clients**: Nombre de clients configurés
- **Rules**: Nombre total de règles de matching

### 2. Filtres
- **All**: Voir tous les emails
- **Matched**: Seulement les emails avec un client identifié
- **Unmatched**: Seulement les emails sans match

### 3. Tableau des emails
Pour chaque email, vous voyez :
- **Email**: Expéditeur (nom et adresse)
- **Subject**: Sujet de l'email
- **Client Match**: Client identifié (ou "No match")
- **Rule**: Règle qui a matché (type + pattern)
- **Confidence**: Score de confiance (0-100%)
- **Received**: Date et heure de réception

#### Indicateur visuel
- ✅ **Fond blanc**: Email correctement traité
- ❌ **Fond rouge**: Incohérence détectée (devrait matcher mais ne matche pas, ou vice versa)

### 4. Vue détaillée
Cliquez sur l'icône 👁️ pour voir :

#### Email Information
- Expéditeur complet
- Date de réception
- Sujet
- Corps du message

#### Pattern Matching Analysis
- **Database Match**: Résultat stocké en base de données
- **Live Test**: Test en temps réel contre TOUTES les règles de TOUS les clients

La section "Live Test" vous montre :
- ✅ **Vert** : La règle matche
- ⚪ **Gris** : La règle ne matche pas

Cela permet de :
1. Vérifier si l'algorithme fonctionne correctement
2. Identifier les faux positifs/négatifs
3. Ajuster les règles si nécessaire

## Types de règles

### 1. DOMAIN (exact)
```
Pattern: amazon.com
Matche: john@amazon.com ✅
Ne matche pas: john@amazon-france.com ❌
```

### 2. SUBDOMAIN
```
Pattern: amazon.com
Matche: john@amazon.com ✅
Matche: john@aws.amazon.com ✅
Matche: john@amazon-france.com ❌
```

### 3. CONTAINS
```
Pattern: amazon
Matche: john@amazon.com ✅
Matche: john@amazon-marketplace.com ✅
Matche: john@myamazon.com ✅
```

### 4. EXACT
```
Pattern: john.doe@amazon.com
Matche: john.doe@amazon.com ✅
Ne matche pas: john@amazon.com ❌
```

## Utilisation pour le debug

### Scénario 1: Vérifier qu'un email est correctement matché
1. Allez dans "All" ou "Matched"
2. Trouvez l'email
3. Vérifiez que "Client Match" affiche le bon client
4. Vérifiez que la "Rule" affichée est correcte
5. Cliquez sur 👁️ pour voir les détails

### Scénario 2: Comprendre pourquoi un email n'est pas matché
1. Allez dans "Unmatched"
2. Trouvez l'email problématique
3. Cliquez sur 👁️
4. Dans "Live Test", regardez si des règles matchent
   - Si une règle matche en live mais pas en DB → Bug dans l'algorithme backend
   - Si aucune règle ne matche → Il faut ajouter une nouvelle règle pour ce client

### Scénario 3: Identifier les faux positifs
1. Allez dans "Matched"
2. Regardez les emails avec fond rouge
3. Ces emails ont un match en DB mais le "Live Test" indique qu'ils ne devraient pas matcher
4. Ajustez les règles pour être plus strictes

## Insérer des données de test

Pour tester l'algorithme, utilisez le script fourni :

```bash
docker exec projectai-backend-1 python insert_test_data.py
```

Ce script crée :
- 3 clients (Amazon, Google, Microsoft)
- 6 règles de matching
- 5 emails de test (4 qui matchent, 1 qui ne matche pas)

## Interprétation des résultats

### ✅ Bon fonctionnement
- Les emails avec `@amazon.com` sont associés au client "Amazon"
- Les emails avec `@google.com` sont associés au client "Google"
- Les emails d'adresses inconnues restent "Unmatched"
- Le score de confiance est élevé (>70%) pour les matches directs

### ⚠️ Problèmes potentiels

#### Problème: Email avec `@amazon.com` ne matche pas
**Causes possibles:**
- La règle n'est pas active (`is_active = false`)
- La règle n'existe pas pour ce client
- Bug dans l'algorithme de matching

**Solution:**
1. Vérifiez les règles du client Amazon dans la base de données
2. Vérifiez que `ClientEmailRule.is_active = true`
3. Testez manuellement le pattern dans le "Live Test"

#### Problème: Email matche le mauvais client
**Causes possibles:**
- Règles trop larges (ex: `CONTAINS` avec un pattern court)
- Plusieurs clients ont des règles qui matchent le même email

**Solution:**
1. Rendez les règles plus spécifiques
2. Utilisez `DOMAIN` plutôt que `CONTAINS` quand possible
3. Ajustez les `confidence_score` pour prioriser certaines règles

## Architecture technique

### Backend
- **Modèle**: `InterceptedEmail` stocke tous les emails
- **Matching**: `ClientEmailRule` définit les règles par client
- **Endpoint**: `GET /email/intercepted` retourne les emails avec debug info

### Frontend
- **Page**: `/ai-monitoring`
- **API**: Appels à `/email/intercepted` et `/clients`
- **Test live**: Algorithme JavaScript qui réplique la logique Python

## Prochaines étapes

Une fois l'algorithme validé :
1. ✅ Déployer la logique de matching en production
2. ✅ Configurer les webhooks Gmail/Outlook
3. ✅ Implémenter la classification IA (couche suivante)
4. ❌ Supprimer cette page de debug

---

**🚨 IMPORTANT**: Cette page expose des informations sensibles (contenu des emails). Ne la déployez JAMAIS en production.

