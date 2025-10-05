from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.config import engine, Base
from app.api import auth, clients, requests, email
from app.models import user, client, request, email_connection, client_email_rule, intercepted_email

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="B2B Request Management API",
    description="API for managing B2B requests between companies",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(requests.router)
app.include_router(email.router)

@app.get("/")
def root():
    return {"message": "B2B Request Management API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
