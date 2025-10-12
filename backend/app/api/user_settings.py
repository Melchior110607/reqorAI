"""
API endpoints pour les paramètres utilisateur (PII, préférences, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import json

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.user_pii_settings import UserPIISettings, PIILevel

router = APIRouter(prefix="/user/settings", tags=["User Settings"])


class PIISettingsResponse(BaseModel):
    protection_level: str
    mask_emails: bool
    mask_phones: bool
    mask_persons: bool
    mask_locations: bool
    mask_dates: bool
    mask_credit_cards: bool
    mask_iban: bool
    mask_urls: bool
    mask_ip_addresses: bool
    context_warning_acknowledged: bool
    enabled_entities: Optional[List[str]] = None


class PIISettingsUpdate(BaseModel):
    protection_level: Optional[str] = None
    mask_emails: Optional[bool] = None
    mask_phones: Optional[bool] = None
    mask_persons: Optional[bool] = None
    mask_locations: Optional[bool] = None
    mask_dates: Optional[bool] = None
    mask_credit_cards: Optional[bool] = None
    mask_iban: Optional[bool] = None
    mask_urls: Optional[bool] = None
    mask_ip_addresses: Optional[bool] = None
    context_warning_acknowledged: Optional[bool] = None


@router.get("/pii", response_model=PIISettingsResponse)
def get_pii_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les paramètres de confidentialité PII de l'utilisateur
    Si aucun paramètre n'existe, crée les valeurs par défaut
    """
    settings = db.query(UserPIISettings).filter(
        UserPIISettings.user_id == current_user.id
    ).first()
    
    # Créer les paramètres par défaut si ils n'existent pas
    if not settings:
        settings = UserPIISettings(
            user_id=current_user.id,
            protection_level=PIILevel.BASIC_REGEX  # Par défaut
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return PIISettingsResponse(
        protection_level=settings.protection_level.value,
        mask_emails=settings.mask_emails,
        mask_phones=settings.mask_phones,
        mask_persons=settings.mask_persons,
        mask_locations=settings.mask_locations,
        mask_dates=settings.mask_dates,
        mask_credit_cards=settings.mask_credit_cards,
        mask_iban=settings.mask_iban,
        mask_urls=settings.mask_urls,
        mask_ip_addresses=settings.mask_ip_addresses,
        context_warning_acknowledged=settings.context_warning_acknowledged,
        enabled_entities=json.loads(settings.enabled_entities) if settings.enabled_entities else None
    )


@router.put("/pii", response_model=PIISettingsResponse)
def update_pii_settings(
    updates: PIISettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour les paramètres de confidentialité PII
    """
    settings = db.query(UserPIISettings).filter(
        UserPIISettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = UserPIISettings(user_id=current_user.id)
        db.add(settings)
    
    # Mettre à jour les champs fournis
    if updates.protection_level is not None:
        try:
            settings.protection_level = PIILevel(updates.protection_level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid protection level: {updates.protection_level}")
    
    if updates.mask_emails is not None:
        settings.mask_emails = updates.mask_emails
    if updates.mask_phones is not None:
        settings.mask_phones = updates.mask_phones
    if updates.mask_persons is not None:
        settings.mask_persons = updates.mask_persons
    if updates.mask_locations is not None:
        settings.mask_locations = updates.mask_locations
    if updates.mask_dates is not None:
        settings.mask_dates = updates.mask_dates
    if updates.mask_credit_cards is not None:
        settings.mask_credit_cards = updates.mask_credit_cards
    if updates.mask_iban is not None:
        settings.mask_iban = updates.mask_iban
    if updates.mask_urls is not None:
        settings.mask_urls = updates.mask_urls
    if updates.mask_ip_addresses is not None:
        settings.mask_ip_addresses = updates.mask_ip_addresses
    if updates.context_warning_acknowledged is not None:
        settings.context_warning_acknowledged = updates.context_warning_acknowledged
    
    # Construire enabled_entities basé sur les flags individuels si en mode CUSTOM
    if settings.protection_level == PIILevel.CUSTOM:
        enabled = []
        if settings.mask_emails:
            enabled.append("EMAIL_ADDRESS")
        if settings.mask_phones:
            enabled.append("PHONE_NUMBER")
        if settings.mask_persons:
            enabled.append("PERSON")
        if settings.mask_locations:
            enabled.append("LOCATION")
        if settings.mask_dates:
            enabled.append("DATE_TIME")
        if settings.mask_credit_cards:
            enabled.append("CREDIT_CARD")
        if settings.mask_iban:
            enabled.append("IBAN_CODE")
        if settings.mask_urls:
            enabled.append("URL")
        if settings.mask_ip_addresses:
            enabled.append("IP_ADDRESS")
        
        settings.enabled_entities = json.dumps(enabled)
    
    db.commit()
    db.refresh(settings)
    
    return PIISettingsResponse(
        protection_level=settings.protection_level.value,
        mask_emails=settings.mask_emails,
        mask_phones=settings.mask_phones,
        mask_persons=settings.mask_persons,
        mask_locations=settings.mask_locations,
        mask_dates=settings.mask_dates,
        mask_credit_cards=settings.mask_credit_cards,
        mask_iban=settings.mask_iban,
        mask_urls=settings.mask_urls,
        mask_ip_addresses=settings.mask_ip_addresses,
        context_warning_acknowledged=settings.context_warning_acknowledged,
        enabled_entities=json.loads(settings.enabled_entities) if settings.enabled_entities else None
    )


@router.get("/pii/info")
def get_pii_info():
    """
    Informations sur les différents niveaux de protection
    et les types de données sensibles
    """
    return {
        "levels": {
            "none": {
                "name": "Aucune protection",
                "description": "Les données sont envoyées telles quelles à l'IA. ⚠️ Maximum de contexte mais aucune confidentialité.",
                "recommended": False,
                "performance": "Très rapide",
                "ai_context": "Maximum"
            },
            "basic_regex": {
                "name": "Protection basique (Regex)",
                "description": "Détection rapide par expressions régulières. Masque les données évidentes (emails, téléphones, cartes bancaires).",
                "recommended": True,
                "performance": "Rapide",
                "ai_context": "Bon",
                "detects": ["Emails", "Téléphones", "IBAN", "Cartes bancaires", "URLs", "Adresses IP", "Dates"]
            },
            "advanced_presidio": {
                "name": "Protection avancée (Presidio + spaCy)",
                "description": "Détection intelligente avec IA. Masque aussi les noms de personnes, lieux, organisations.",
                "recommended": True,
                "performance": "Moyen",
                "ai_context": "Moyen",
                "detects": ["Tout ce qui précède", "Noms de personnes", "Lieux", "Organisations", "Numéros d'identification"]
            },
            "custom": {
                "name": "Configuration personnalisée",
                "description": "Choisissez précisément quelles données masquer.",
                "recommended": False,
                "performance": "Variable",
                "ai_context": "Variable"
            }
        },
        "pii_types": {
            "EMAIL_ADDRESS": {"name": "Adresses email", "example": "jean.dupont@example.com → <EMAIL>", "recommended": True},
            "PHONE_NUMBER": {"name": "Numéros de téléphone", "example": "+41 79 123 45 67 → <PHONE>", "recommended": True},
            "PERSON": {"name": "Noms de personnes", "example": "Jean Dupont → <PERSON>", "recommended": False, "warning": "Réduit le contexte"},
            "LOCATION": {"name": "Lieux et adresses", "example": "Rue du Commerce 5, Lausanne → <LOCATION>", "recommended": False, "warning": "Peut être utile pour le contexte"},
            "DATE_TIME": {"name": "Dates", "example": "12/10/2025 → <DATE>", "recommended": False, "warning": "Les dates sont souvent importantes"},
            "CREDIT_CARD": {"name": "Numéros de carte", "example": "4532 1234 5678 9010 → <CREDIT_CARD>", "recommended": True},
            "IBAN_CODE": {"name": "IBAN", "example": "CH93 0076 2011 6238 5295 7 → <IBAN>", "recommended": True},
            "URL": {"name": "URLs", "example": "https://example.com → <URL>", "recommended": False},
            "IP_ADDRESS": {"name": "Adresses IP", "example": "192.168.1.1 → <IP>", "recommended": False}
        },
        "warning": "⚠️ Important : Plus vous masquez de données, moins l'IA aura de contexte pour bien comprendre et classifier vos emails. Trouvez le bon équilibre entre confidentialité et efficacité."
    }

