from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, Token, PasswordReset
from security import get_password_hash, verify_password, create_access_token
from dependencies import get_current_active_user
from routers import upload as upload_router
from routers import process_mining as process_mining_router
from routers import anomaly as anomaly_router
from routers import explanations as explanations_router
from routers import reports as reports_router

app = FastAPI(title="FlowGuard AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router.router, prefix="/upload", tags=["Upload"])
app.include_router(process_mining_router.router, prefix="/process-mine", tags=["Process Mining"])
app.include_router(anomaly_router.router, prefix="/anomaly", tags=["Anomaly Detection"])
app.include_router(explanations_router.router, prefix="/explanations", tags=["Explainable AI"])
app.include_router(reports_router.router, prefix="/reports", tags=["Reports"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(data={"sub": user.email, "role": role_value})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/logout")
def logout():
    # Since we are using stateless JWTs without a Redis blocklist for Phase 1,
    # the client is responsible for deleting the token.
    return {"message": "Successfully logged out. Please remove the token on the client side."}

@app.post("/auth/reset-password")
def reset_password(
    payload: PasswordReset, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
