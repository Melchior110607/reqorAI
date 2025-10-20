"""
Imports centralisés de tous les modèles pour éviter les imports circulaires
Importer ce module résout tous les relationships SQLAlchemy
"""
from app.models.user import User
from app.models.client import Client
from app.models.request import Request
from app.models.email_connection import EmailConnection
from app.models.client_email_rule import ClientEmailRule
from app.models.intercepted_email import InterceptedEmail
from app.models.sync_log import SyncLog
from app.models.user_pii_settings import UserPIISettings
from app.models.webhook_subscription import WebhookSubscription
from app.models.knowledge_base import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk

__all__ = [
    'User',
    'Client', 
    'Request',
    'EmailConnection',
    'ClientEmailRule',
    'InterceptedEmail',
    'SyncLog',
    'UserPIISettings',
    'WebhookSubscription',
    'KnowledgeDocument',
    'KnowledgeChunk'
]

