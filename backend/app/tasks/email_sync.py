"""
Tâches Celery pour la synchronisation automatique des emails
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database.config import SessionLocal

# IMPORTANT: Import tous les modèles pour résoudre les relationships SQLAlchemy
import app.models  # Charge tous les modèles

from app.models.email_connection import EmailConnection, EmailProvider, ConnectionStatus
from app.models.sync_log import SyncLog
from app.services.gmail_service import GmailService, NetworkError as GmailNetworkError, AuthenticationError as GmailAuthError
from app.services.outlook_service import OutlookService, NetworkError as OutlookNetworkError, AuthenticationError as OutlookAuthError
from app.services.email_service import EmailProcessingService

# Seuils de gestion d'erreurs
MAX_CONSECUTIVE_FAILURES = 5  # Marquer ERROR après 5 échecs consécutifs
NETWORK_ERROR_THRESHOLD = 3  # Ignorer les 3 premières erreurs réseau


@celery_app.task(name='app.tasks.email_sync.sync_all_user_emails')
def sync_all_user_emails():
    """
    Tâche périodique : Synchronise les emails de tous les utilisateurs
    OPTIMISÉ : Limite à 10 emails par connexion pour ne pas surcharger
    """
    db = SessionLocal()
    try:
        # Récupérer toutes les connexions actives (distinct pour éviter doublons)
        connections = db.query(EmailConnection).filter(
            EmailConnection.status == ConnectionStatus.ACTIVE
        ).distinct().all()
        
        # OPTIMISATION: Si aucune connexion, ne rien faire
        if not connections:
            print("ℹ️ Aucune connexion active, sync ignorée")
            return {'message': 'No active connections'}
        
        total_synced = 0
        total_duplicates = 0
        results = []
        
        for connection in connections:
            try:
                result = sync_connection_emails(connection.id, db)
                total_synced += result['synced']
                total_duplicates += result['duplicates']
                results.append({
                    'connection_id': connection.id,
                    'email': connection.email_address,
                    'provider': connection.provider.value,
                    'synced': result['synced'],
                    'duplicates': result['duplicates']
                })
            except Exception as e:
                print(f"❌ Erreur sync connection {connection.id}: {str(e)}")
                results.append({
                    'connection_id': connection.id,
                    'email': connection.email_address,
                    'provider': connection.provider.value,
                    'error': str(e)
                })
        
        print(f"✅ Sync automatique terminée: {total_synced} nouveaux emails, {total_duplicates} doublons évités")
        
        # Enregistrer le log de sync
        sync_log = SyncLog(
            sync_type="auto",
            total_synced=total_synced,
            total_duplicates=total_duplicates,
            connections_processed=len(connections),
            details=results
        )
        db.add(sync_log)
        db.commit()
        
        return {
            'total_synced': total_synced,
            'total_duplicates': total_duplicates,
            'connections_processed': len(connections),
            'details': results,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print(f"❌ Erreur sync globale: {str(e)}")
        return {'error': str(e)}
    finally:
        db.close()


def sync_connection_emails(connection_id: int, db: Session) -> dict:
    """
    Synchronise les emails d'une connexion spécifique
    OPTIMISÉ : Limite à 10 emails par sync pour performance
    RÉSILIENT : Gère les erreurs réseau sans casser la connexion
    """
    connection = db.query(EmailConnection).filter(
        EmailConnection.id == connection_id
    ).first()
    
    if not connection:
        raise Exception(f"Connection {connection_id} not found")
    
    # Récupérer depuis la dernière sync
    since_timestamp = connection.last_sync if connection.last_sync else None
    
    # OPTIMISATION: Limite à 10 emails max par sync (toutes les minutes)
    # Avec sync chaque minute, 10 emails/min = 600 emails/heure max
    max_emails = 10
    
    try:
        # Appeler le service approprié
        if connection.provider == EmailProvider.GMAIL:
            gmail_service = GmailService(db)
            emails = gmail_service.get_recent_emails(
                connection, 
                max_results=max_emails,
                since_timestamp=since_timestamp
            )
        elif connection.provider == EmailProvider.OUTLOOK:
            outlook_service = OutlookService(db)
            emails = outlook_service.get_recent_emails(
                connection, 
                max_results=max_emails,
                since_timestamp=since_timestamp
            )
        else:
            raise Exception(f"Unsupported provider: {connection.provider}")
        
        # Traiter les emails avec anti-doublon
        processing_service = EmailProcessingService(db)
        synced = 0
        duplicates = 0
        
        for email_data in emails:
            result = processing_service.process_intercepted_email(
                email_data, 
                connection.id, 
                connection.user_id
            )
            if result:
                synced += 1
            else:
                duplicates += 1
        
        # ✅ SUCCÈS : Réinitialiser le compteur d'échecs
        connection.consecutive_failures = 0
        connection.last_error = None
        connection.last_sync = datetime.now(timezone.utc)
        
        # Réactiver la connexion si elle était en ERROR
        if connection.status == ConnectionStatus.ERROR:
            connection.status = ConnectionStatus.ACTIVE
            print(f"✅ Connexion {connection.id} ({connection.email_address}) réactivée après succès")
        
        db.commit()
        
        return {'synced': synced, 'duplicates': duplicates}
    
    except (GmailNetworkError, OutlookNetworkError) as e:
        # 🌐 ERREUR RÉSEAU TEMPORAIRE : Incrémenter mais ne pas paniquer
        connection.consecutive_failures += 1
        connection.last_error = str(e)
        
        if connection.consecutive_failures < NETWORK_ERROR_THRESHOLD:
            # Erreur réseau mais on tolère
            print(f"🌐 Erreur réseau temporaire {connection.consecutive_failures}/{NETWORK_ERROR_THRESHOLD} pour {connection.email_address}: {str(e)}")
            connection.status = ConnectionStatus.ACTIVE  # Garder ACTIVE
        elif connection.consecutive_failures < MAX_CONSECUTIVE_FAILURES:
            # Trop d'erreurs réseau, passer en INACTIVE (soft)
            print(f"⚠️ Erreurs réseau répétées {connection.consecutive_failures}/{MAX_CONSECUTIVE_FAILURES} pour {connection.email_address}")
            connection.status = ConnectionStatus.INACTIVE
        else:
            # Vraiment trop d'échecs, marquer ERROR
            print(f"❌ Trop d'erreurs consécutives ({connection.consecutive_failures}) pour {connection.email_address}, marqué ERROR")
            connection.status = ConnectionStatus.ERROR
        
        db.commit()
        raise  # Réamorcer pour logging
    
    except (GmailAuthError, OutlookAuthError) as e:
        # 🔐 ERREUR D'AUTHENTIFICATION : Plus sérieux, incrémenter rapidement
        connection.consecutive_failures += 2  # Compter double
        connection.last_error = f"Auth error: {str(e)}"
        
        if connection.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            connection.status = ConnectionStatus.ERROR
            print(f"🔐 Erreur d'authentification pour {connection.email_address}, marqué ERROR après {connection.consecutive_failures} échecs")
        else:
            connection.status = ConnectionStatus.INACTIVE
            print(f"🔐 Erreur d'authentification pour {connection.email_address}, marqué INACTIVE ({connection.consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
        
        db.commit()
        raise
    
    except Exception as e:
        # ❌ ERREUR INATTENDUE : Incrémenter et logger
        connection.consecutive_failures += 1
        connection.last_error = f"Unexpected: {str(e)}"
        
        if connection.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            connection.status = ConnectionStatus.ERROR
            print(f"❌ Erreur inattendue pour {connection.email_address}, marqué ERROR après {connection.consecutive_failures} échecs: {str(e)}")
        else:
            print(f"⚠️ Erreur pour {connection.email_address} ({connection.consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}): {str(e)}")
        
        db.commit()
        raise


@celery_app.task(name='app.tasks.email_sync.sync_user_emails')
def sync_user_emails(user_id: int):
    """
    Synchronise les emails d'un utilisateur spécifique
    Peut être appelée manuellement ou via webhook
    """
    db = SessionLocal()
    try:
        connections = db.query(EmailConnection).filter(
            EmailConnection.user_id == user_id,
            EmailConnection.status == ConnectionStatus.ACTIVE
        ).all()
        
        total_synced = 0
        total_duplicates = 0
        
        for connection in connections:
            try:
                result = sync_connection_emails(connection.id, db)
                total_synced += result['synced']
                total_duplicates += result['duplicates']
            except Exception as e:
                print(f"❌ Erreur sync connection {connection.id}: {str(e)}")
        
        return {
            'user_id': user_id,
            'total_synced': total_synced,
            'total_duplicates': total_duplicates,
            'connections_processed': len(connections)
        }
        
    except Exception as e:
        print(f"❌ Erreur sync user {user_id}: {str(e)}")
        return {'error': str(e)}
    finally:
        db.close()

