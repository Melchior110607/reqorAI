# 📧 Email Interception Debug - Simple

## Objectif

**PHASE 1** : Vérifier que les emails Gmail sont bien interceptés via le webhook.

Cette page affiche simplement **TOUS les emails** du compte Gmail connecté qui ont été interceptés.

## Accès

🔗 http://localhost:3000/ai-monitoring

## Ce que vous voyez

- **Nombre total d'emails** interceptés
- **Liste des emails** avec :
  - Expéditeur (nom + email)
  - Sujet
  - Aperçu du corps (200 premiers caractères)
  - Date de réception
- **Détails complets** en cliquant sur l'œil 👁️

## Comment tester

1. **Connectez-vous** avec votre compte Gmail (OAuth)
2. **Envoyez un email** à votre adresse Gmail
3. **Attendez 10-30 secondes** (délai du webhook)
4. **Rafraîchissez** la page
5. **L'email devrait apparaître** dans la liste

## Prochaine étape

Une fois que les emails apparaissent correctement ici :

→ **PHASE 2** : Ajouter l'algorithme de matching client par-dessus

Pour l'instant, **on ne fait RIEN avec les emails**, on vérifie juste qu'ils arrivent !

## Données de test

Les données créées avec `insert_test_data.py` sont visibles ici.

## Troubleshooting

### Aucun email n'apparaît

**Vérifiez** :
1. Que vous êtes bien connecté avec Gmail OAuth
2. Que le webhook Gmail est configuré (voir Google Cloud Console)
3. Les logs du backend : `docker logs projectai-backend-1`

### Les emails mettent du temps à apparaître

C'est normal ! Le webhook Gmail peut prendre 10-30 secondes pour notifier le backend.

