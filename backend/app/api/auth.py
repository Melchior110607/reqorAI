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
            # Authentification principale - utiliser la logique email existante temporairement
            # TODO: Implémenter logique complète avec get_user_info depuis Google
            gmail_service = GmailService(db)
            auth_service = AuthService(db)
            
            # Pour l'instant, créer avec callback normal et récupérer l'email de la connexion
            connection = gmail_service.handle_oauth_callback(code, "temp_user")
            
            # Récupérer l'utilisateur de la connexion
            user = db.query(User).filter(User.email == connection.email_address).first()
            
            if not user:
                # Créer un nouvel utilisateur OAuth
                user = User(
                    email=connection.email_address,
                    company_name="My Company",
                    auth_provider=AuthProvider.GOOGLE,
                    oauth_provider_id=connection.email_address  # Temporaire
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Associer la connexion au nouvel utilisateur
                connection.user_id = user.id
                db.commit()
            
            # Générer token JWT
            access_token = auth_service.create_access_token(user.email)
            
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
            # Authentification principale - utiliser la logique email existante temporairement
            # TODO: Implémenter logique complète avec get_user_info depuis Microsoft
            outlook_service = OutlookService(db)
            auth_service = AuthService(db)
            
            # Pour l'instant, créer avec callback normal et récupérer l'email de la connexion
            connection = outlook_service.handle_oauth_callback(code, "temp_user")
            
            # Récupérer l'utilisateur de la connexion
            user = db.query(User).filter(User.email == connection.email_address).first()
            
            if not user:
                # Créer un nouvel utilisateur OAuth
                user = User(
                    email=connection.email_address,
                    company_name="My Company",
                    auth_provider=AuthProvider.MICROSOFT,
                    oauth_provider_id=connection.email_address  # Temporaire
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Associer la connexion au nouvel utilisateur
                connection.user_id = user.id
                db.commit()
            
            # Générer token JWT
            access_token = auth_service.create_access_token(user.email)
            
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
