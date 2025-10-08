# 🗄️ Guide d'Accès à la Base de Données PostgreSQL

## 📌 Informations de Connexion

```
Host: localhost
Port: 5432
Database: b2b_requests
User: postgres
Password: postgres
```

---

## 🚀 Méthodes d'Accès

### 1️⃣ Via Docker (Recommandé - Le Plus Simple)

#### A. Accès interactif (psql)

```bash
# Ouvrir un terminal psql dans le container
docker exec -it projectai-postgres-1 psql -U postgres -d b2b_requests
```

Vous serez dans un terminal PostgreSQL interactif :
```sql
b2b_requests=# SELECT * FROM email_connections;
b2b_requests=# \dt  -- Liste toutes les tables
b2b_requests=# \d email_connections  -- Détails d'une table
b2b_requests=# \q  -- Quitter
```

#### B. Exécuter une commande SQL unique

```bash
# Exécuter une requête directement
docker exec -it projectai-postgres-1 psql -U postgres -d b2b_requests -c "SELECT * FROM email_connections;"
```

#### C. Exécuter un fichier SQL

```bash
# Exécuter un script SQL (ex: reset_outlook_connection.sql)
docker exec -i projectai-postgres-1 psql -U postgres -d b2b_requests < reset_outlook_connection.sql
```

---

### 2️⃣ Via Client GUI (DBeaver, pgAdmin, TablePlus, etc.)

#### Configuration dans DBeaver/TablePlus :
```
Type: PostgreSQL
Host: localhost
Port: 5432
Database: b2b_requests
Username: postgres
Password: postgres
```

**Avantage** : Interface graphique, exploration facile des données.

---

### 3️⃣ Via `psql` Local (Si installé sur ta machine)

```bash
psql -h localhost -p 5432 -U postgres -d b2b_requests
# Password: postgres
```

---

## 🛠️ Commandes Utiles

### Voir toutes les tables
```sql
\dt
```

### Structure d'une table
```sql
\d email_connections
```

### Voir toutes les connexions email
```sql
SELECT 
    id,
    user_id,
    provider,
    email_address,
    status,
    consecutive_failures,
    last_error,
    last_sync
FROM email_connections;
```

### Réinitialiser une connexion Outlook en ERROR
```sql
UPDATE email_connections 
SET 
    status = 'active',
    consecutive_failures = 0,
    last_error = NULL
WHERE id = 2;  -- Remplacer par l'ID de ta connexion
```

### Voir tous les emails interceptés
```sql
SELECT 
    id,
    sender_email,
    subject,
    email_received_at,
    matched_client_id,
    rule_type
FROM intercepted_emails
ORDER BY email_received_at DESC
LIMIT 10;
```

### Voir les logs de synchronisation
```sql
SELECT 
    id,
    sync_type,
    total_synced,
    total_duplicates,
    connections_processed,
    created_at
FROM sync_logs
ORDER BY created_at DESC
LIMIT 10;
```

### Statistiques de la base de données
```sql
-- Taille de la base
SELECT pg_database_size('b2b_requests') AS size_bytes,
       pg_size_pretty(pg_database_size('b2b_requests')) AS size_human;

-- Nombre de rows par table
SELECT 
    schemaname,
    tablename,
    n_tup_ins AS inserts,
    n_tup_upd AS updates,
    n_tup_del AS deletes,
    n_live_tup AS live_rows
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

---

## 🔧 Scripts de Réparation Rapide

### Réinitialiser toutes les connexions en ERROR
```bash
docker exec -i projectai-postgres-1 psql -U postgres -d b2b_requests < reset_outlook_connection.sql
```

### Supprimer tous les doublons d'emails (si nécessaire)
```sql
DELETE FROM intercepted_emails a
WHERE a.id NOT IN (
    SELECT MIN(b.id)
    FROM intercepted_emails b
    WHERE b.message_id = a.message_id
);
```

### Réinitialiser les compteurs d'échecs pour toutes les connexions
```sql
UPDATE email_connections 
SET 
    consecutive_failures = 0,
    last_error = NULL,
    status = 'active'
WHERE status IN ('error', 'inactive');
```

---

## 🚨 Dépannage Courant

### Problème : "could not connect to server"
**Solution** : Vérifier que le container PostgreSQL est en cours d'exécution :
```bash
docker ps | grep postgres
```

Si non actif :
```bash
docker-compose up -d postgres
```

### Problème : "database b2b_requests does not exist"
**Solution** : Recréer la base :
```bash
docker-compose down
docker volume rm projectai_postgres_data
docker-compose up -d
```

### Problème : "permission denied"
**Solution** : S'assurer d'utiliser le bon user (postgres) et le bon mot de passe.

---

## 📊 Monitoring en Production

### Voir les connexions actives
```sql
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query
FROM pg_stat_activity
WHERE datname = 'b2b_requests';
```

### Voir les requêtes lentes (> 1 seconde)
```sql
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query
FROM pg_stat_activity
WHERE state = 'active' 
  AND now() - pg_stat_activity.query_start > interval '1 second';
```

---

## 🎯 Cas d'Usage Spécifiques

### 1. Ta connexion Outlook est en ERROR

```bash
# Méthode 1 : Via script
docker exec -i projectai-postgres-1 psql -U postgres -d b2b_requests < reset_outlook_connection.sql

# Méthode 2 : Commande directe
docker exec -it projectai-postgres-1 psql -U postgres -d b2b_requests -c "
UPDATE email_connections 
SET status = 'active', consecutive_failures = 0, last_error = NULL
WHERE provider = 'outlook' AND status = 'error';
"
```

### 2. Vérifier si les emails sont bien synchronisés

```bash
docker exec -it projectai-postgres-1 psql -U postgres -d b2b_requests -c "
SELECT 
    COUNT(*) as total_emails,
    COUNT(DISTINCT sender_email) as unique_senders,
    MAX(email_received_at) as last_email_date
FROM intercepted_emails;
"
```

### 3. Voir les erreurs de synchronisation récentes

```bash
docker exec -it projectai-postgres-1 psql -U postgres -d b2b_requests -c "
SELECT 
    id,
    email_address,
    status,
    consecutive_failures,
    last_error,
    last_sync
FROM email_connections
WHERE consecutive_failures > 0
ORDER BY consecutive_failures DESC;
"
```

---

## 💡 Conseils Pro

1. **Toujours faire un backup avant des modifications importantes** :
   ```bash
   docker exec projectai-postgres-1 pg_dump -U postgres b2b_requests > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Utiliser des transactions pour les updates critiques** :
   ```sql
   BEGIN;
   UPDATE email_connections SET status = 'active' WHERE id = 2;
   -- Vérifier le résultat
   SELECT * FROM email_connections WHERE id = 2;
   -- Si OK : COMMIT; sinon : ROLLBACK;
   COMMIT;
   ```

3. **Ne jamais supprimer de données en production sans backup**.

4. **Pour les requêtes complexes, tester d'abord avec `SELECT` avant `UPDATE/DELETE`**.

---

## 📚 Ressources Supplémentaires

- [Documentation PostgreSQL](https://www.postgresql.org/docs/)
- [psql Commands Cheat Sheet](https://postgrescheatsheet.com/)
- [DBeaver Download](https://dbeaver.io/download/)

---

**Questions ?** Ce guide couvre 99% des cas d'usage. Pour des besoins spécifiques, utilise le terminal psql interactif et explore ! 🚀

