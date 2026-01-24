from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from .database import engine, get_db, Base
from .models import User, UserRole
from .schemas import (
    RegisterRequest, LoginRequest, RefreshTokenRequest,
    ChangePasswordRequest, UpdateProfileRequest,
    UserResponse, TokenResponse, LoginResponse, MessageResponse
)
from .security import (
    verify_access_token, require_role, require_admin,
    create_access_token, create_refresh_token
)
from .services import UserService, TokenService

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IAM Service",
    description="Identity and Access Management Service",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Create all database tables on startup"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# ==================== Authentication Endpoints ====================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    user = UserService.register_user(db, req)
    return user

@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return tokens"""
    user = UserService.authenticate_user(db, req.email, req.password)
    
    access_token, access_expires = create_access_token(
        user.email, user.role.value, str(user.id)
    )
    refresh_token, refresh_expires = create_refresh_token(
        user.email, user.role.value, str(user.id)
    )
    
    # Store refresh token
    TokenService.store_refresh_token(db, user.id, refresh_token, refresh_expires)
    
    return {
        "user": UserResponse.from_orm(user),
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": access_expires
        }
    }

@app.post("/auth/refresh", response_model=TokenResponse)
def refresh_tokens(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    payload = TokenService.verify_refresh_token(db, req.refresh_token)
    
    user = UserService.get_user_by_email(db, payload["sub"])
    
    access_token, access_expires = create_access_token(
        user.email, user.role.value, str(user.id)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": req.refresh_token,
        "expires_in": access_expires
    }

@app.post("/auth/logout")
def logout(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Logout user (revoke refresh token)"""
    TokenService.revoke_refresh_token(db, req.refresh_token)
    return {"message": "Logged out successfully", "success": True}

@app.post("/auth/logout-all")
def logout_all(current_user: dict = Depends(verify_access_token), db: Session = Depends(get_db)):
    """Logout from all devices (revoke all tokens)"""
    TokenService.revoke_user_tokens(db, current_user["user_id"])
    return {"message": "Logged out from all devices", "success": True}

# ==================== User Profile Endpoints ====================

@app.get("/users/me", response_model=UserResponse)
def get_current_user(current_user: dict = Depends(verify_access_token), db: Session = Depends(get_db)):
    """Get current user profile"""
    user = UserService.get_user_by_id(db, current_user["user_id"])
    return user

@app.put("/users/me", response_model=UserResponse)
def update_current_user(
    req: UpdateProfileRequest,
    current_user: dict = Depends(verify_access_token),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    user = UserService.update_user_profile(
        db, current_user["user_id"], req.full_name, req.role
    )
    return user

@app.post("/users/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: dict = Depends(verify_access_token),
    db: Session = Depends(get_db)
):
    """Change current user password"""
    UserService.change_password(db, current_user["user_id"], req.old_password, req.new_password)
    return {"message": "Password changed successfully", "success": True}

@app.post("/users/deactivate")
def deactivate_account(
    current_user: dict = Depends(verify_access_token),
    db: Session = Depends(get_db)
):
    """Deactivate current user account"""
    UserService.deactivate_account(db, current_user["user_id"])
    return {"message": "Account deactivated successfully", "success": True}

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID (public endpoint)"""
    user = UserService.get_user_by_id(db, user_id)
    return user

# ==================== Admin Endpoints ====================

@app.get("/admin/users")
def list_all_users(current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """List all users (admin only)"""
    users = db.query(User).all()
    return [UserResponse.from_orm(u) for u in users]

@app.put("/admin/users/{user_id}/role")
def update_user_role(
    user_id: str,
    role: UserRole,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user role (admin only)"""
    user = UserService.update_user_profile(db, user_id, role=role)
    return user

@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate user (admin only)"""
    user = UserService.deactivate_account(db, user_id)
    return {"message": f"User {user_id} deactivated", "success": True}
# ==================== Health Check ====================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "iam-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)