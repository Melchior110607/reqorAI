"""
Modèle pour les paramètres de confidentialité PII de l'utilisateur
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database.config import Base
import enum


class PIILevel(str, enum.Enum):
    """Niveaux de protection des données sensibles"""
    NONE = "none"  # Pas de masquage (données brutes envoyées à l'IA)
    BASIC_REGEX = "basic_regex"  # Regex basique rapide
    ADVANCED_PRESIDIO = "advanced_presidio"  # Presidio avec spaCy (plus précis)
    CUSTOM = "custom"  # Configuration personnalisée
    
    # Trick: return lowercase value
    def __str__(self):
        return self.value


class UserPIISettings(Base):
    """
    Configuration de la protection des données sensibles par utilisateur
    """
    __tablename__ = "user_pii_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Niveau de protection global
    # Note: SQLAlchemy Enum doit utiliser les VALEURS de l'enum Python, pas les noms
    protection_level = Column(
        SQLEnum(PIILevel, name='pii_level', values_callable=lambda x: [e.value for e in x]),
        default=PIILevel.BASIC_REGEX,
        nullable=False
    )
    
    # Configuration personnalisée (si protection_level = CUSTOM)
    # JSON array des types de PII à masquer
    # Ex: ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD"]
    enabled_entities = Column(Text)  # JSON array
    
    # Options individuelles (pour UI granulaire)
    mask_emails = Column(Boolean, default=True)
    mask_phones = Column(Boolean, default=True)
    mask_persons = Column(Boolean, default=False)  # Noms de personnes
    mask_locations = Column(Boolean, default=False)  # Adresses
    mask_dates = Column(Boolean, default=False)  # Dates
    mask_credit_cards = Column(Boolean, default=True)
    mask_iban = Column(Boolean, default=True)
    mask_urls = Column(Boolean, default=False)
    mask_ip_addresses = Column(Boolean, default=False)
    
    # Message d'avertissement accepté
    context_warning_acknowledged = Column(Boolean, default=False)
    
    # Relation
    user = relationship("User", back_populates="pii_settings")


# Ajouter la relation dans le modèle User
# (à ajouter manuellement dans app/models/user.py)
# pii_settings = relationship("UserPIISettings", back_populates="user", uselist=False)

