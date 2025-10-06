from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database.config import get_db, settings
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.services.gmail_service import GmailService
from app.services.outlook_service import OutlookService
from app.api.dependencies import get_current_user
from app.models.user import User, AuthProvider
from app.auth.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.register_user(user_data)
    return user

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    access_token = auth_service.authenticate_user(login_data)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_current_user(
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    # Update allowed fields
    allowed_fields = ['company_name', 'first_name', 'last_name', 'phone']
    for field in allowed_fields:
        if field in update_data:
            setattr(current_user, field, update_data[field])
    
    db.commit()
    db.refresh(current_user)
    return current_user

# OAuth Authentication Routes
@router.get("/oauth/google")
def google_oauth_login(db: Session = Depends(get_db)):
    """
    Démarre le flow OAuth Google pour l'authentification principale
    """
    try:
        gmail_service = GmailService(db)
        # Utiliser user_id spécial pour indiquer authentification principale
        auth_url = gmail_service.get_auth_url(user_id=-1)  # -1 = primary auth
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/oauth/microsoft")
def microsoft_oauth_login(db: Session = Depends(get_db)):
    """
    Démarre le flow OAuth Microsoft pour l'authentification principale
    """
    try:
        outlook_service = OutlookService(db)
        # Utiliser user_id spécial pour indiquer authentification principale  
        auth_url = outlook_service.get_auth_url(user_id=-1)  # -1 = primary auth
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/oauth/callback/google")
def google_oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """
    Callback OAuth Google - Crée ou connecte l'utilisateur
    """
    try:
        # Vérifier si état indique authentification principale ou ajout de canal
        is_primary_auth = (state == "-1")
        
        if is_primary_auth:
            # Authentification principale
            gmail_service = GmailService(db)
            auth_service = AuthService(db)
            
            # Échanger le code contre les credentials
            client_config = {
                "web": {
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [f"{settings.base_url}/auth/oauth/callback/google"]
                }
            }
            
            from google_auth_oauthlib.flow import Flow
            flow = Flow.from_client_config(client_config, scopes=gmail_service.scopes)
            flow.redirect_uri = f"{settings.base_url}/auth/oauth/callback/google"
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            # Obtenir les infos utilisateur
            from googleapiclient.discovery import build
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()
            email_address = profile['emailAddress']
            
            # Chercher ou créer l'utilisateur
            user = db.query(User).filter(User.email == email_address).first()
            
            if not user:
                # Créer un nouvel utilisateur OAuth
                # Extraire le nom d'entreprise de l'email (sans .com, .fr, etc.)
                domain = email_address.split('@')[1] if '@' in email_address else "My Company"
                company_name = domain.split('.')[0].capitalize() if '.' in domain else domain.capitalize()
                
                user = User(
                    email=email_address,
                    company_name=company_name,
                    auth_provider=AuthProvider.GOOGLE,
                    oauth_provider_id=email_address
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Créer ou mettre à jour la connexion email
            from app.models.email_connection import EmailConnection, EmailProvider, ConnectionStatus
            connection = db.query(EmailConnection).filter(
                EmailConnection.user_id == user.id,
                EmailConnection.email_address == email_address
            ).first()
            
            if not connection:
                connection = EmailConnection(
                    user_id=user.id,
                    provider=EmailProvider.GMAIL,
                    email_address=email_address,
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    expires_at=credentials.expiry,
                    status=ConnectionStatus.ACTIVE
                )
                db.add(connection)
            else:
                connection.access_token = credentials.token
                connection.refresh_token = credentials.refresh_token
                connection.expires_at = credentials.expiry
                connection.status = ConnectionStatus.ACTIVE
            
            db.commit()
            
            # Générer token JWT
            access_token = create_access_token(data={"sub": user.email})
            
            # Rediriger vers frontend avec token
            return RedirectResponse(
                url=f"{settings.frontend_url}/oauth-success?token={access_token}&provider=google"
            )
        else:
            # Ajout de canal email supplémentaire (déjà implémenté dans email.py)
            raise HTTPException(status_code=400, detail="Use /email/callback/gmail for adding email channels")
            
    except Exception as e:
        print(f"OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error={str(e)}"
        )

@router.get("/oauth/callback/microsoft")
def microsoft_oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """
    Callback OAuth Microsoft - Crée ou connecte l'utilisateur
    """
    try:
        # Vérifier si état indique authentification principale ou ajout de canal
        is_primary_auth = (state == "-1")
        
        if is_primary_auth:
            # Authentification principale
            outlook_service = OutlookService(db)
            auth_service = AuthService(db)
            
            # Échanger le code contre le token
            import requests
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            redirect_uri = f"{settings.base_url}/auth/oauth/callback/microsoft"
            
            token_data = {
                'client_id': settings.outlook_client_id,
                'client_secret': settings.outlook_client_secret,
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
                'scope': ' '.join(outlook_service.scopes)
            }
            
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()
            
            access_token_ms = token_info['access_token']
            
            # Obtenir les infos utilisateur
            user_info_response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={'Authorization': f'Bearer {access_token_ms}'}
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()
            
            email_address = user_info['mail'] or user_info['userPrincipalName']
            
            # Chercher ou créer l'utilisateur
            user = db.query(User).filter(User.email == email_address).first()
            
            if not user:
                # Créer un nouvel utilisateur OAuth
                # Extraire le nom d'entreprise de l'email (sans .com, .fr, etc.)
                domain = email_address.split('@')[1] if '@' in email_address else "My Company"
                company_name = domain.split('.')[0].capitalize() if '.' in domain else domain.capitalize()
                
                user = User(
                    email=email_address,
                    company_name=company_name,
                    auth_provider=AuthProvider.MICROSOFT,
                    oauth_provider_id=user_info['id']
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Créer ou mettre à jour la connexion email
            from app.models.email_connection import EmailConnection, EmailProvider, ConnectionStatus
            from datetime import datetime, timedelta
            
            connection = db.query(EmailConnection).filter(
                EmailConnection.user_id == user.id,
                EmailConnection.email_address == email_address
            ).first()
            
            expires_at = datetime.now() + timedelta(seconds=token_info.get('expires_in', 3600))
            
            if not connection:
                connection = EmailConnection(
                    user_id=user.id,
                    provider=EmailProvider.OUTLOOK,
                    email_address=email_address,
                    access_token=access_token_ms,
                    refresh_token=token_info.get('refresh_token'),
                    expires_at=expires_at,
                    status=ConnectionStatus.ACTIVE
                )
                db.add(connection)
            else:
                connection.access_token = access_token_ms
                connection.refresh_token = token_info.get('refresh_token')
                connection.expires_at = expires_at
                connection.status = ConnectionStatus.ACTIVE
            
            db.commit()
            
            # Générer token JWT
            access_token = create_access_token(data={"sub": user.email})
            
            # Rediriger vers frontend avec token
            return RedirectResponse(
                url=f"{settings.frontend_url}/oauth-success?token={access_token}&provider=microsoft"
            )
        else:
            # Ajout de canal email supplémentaire (déjà implémenté dans email.py)
            raise HTTPException(status_code=400, detail="Use /email/callback/outlook for adding email channels")
            
    except Exception as e:
        print(f"OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error={str(e)}"
        )
