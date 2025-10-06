from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.config import get_db
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.models.client import Client
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.post("/", response_model=ClientResponse)
def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_client = Client(**client_data.dict(), user_id=current_user.id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.get("/", response_model=List[ClientResponse])
def get_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.client_email_rule import ClientEmailRule
    
    clients = db.query(Client).filter(Client.user_id == current_user.id).all()
    
    # Enrichir avec les règles email pour chaque client
    clients_with_rules = []
    for client in clients:
        client_dict = {
            "id": client.id,
            "user_id": client.user_id,
            "name": client.name,
            "company": client.company,
            "email": client.email,
            "phone": client.phone,
            "address": client.address,
            "created_at": client.created_at,
            "updated_at": client.updated_at,
            "email_rules": []
        }
        
        # Récupérer les règles email pour ce client
        rules = db.query(ClientEmailRule).filter(
            ClientEmailRule.client_id == client.id
        ).all()
        
        client_dict["email_rules"] = [{
            "id": rule.id,
            "rule_type": rule.rule_type,
            "pattern": rule.pattern,
            "confidence_score": rule.confidence_score,
            "is_active": rule.is_active
        } for rule in rules]
        
        clients_with_rules.append(client_dict)
    
    return clients_with_rules

@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_update: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    update_data = client_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    return client

@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    db.delete(client)
    db.commit()
    return {"message": "Client deleted successfully"}
