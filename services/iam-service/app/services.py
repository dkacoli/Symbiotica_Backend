from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from .models import User, UserRole, RefreshToken
from .security import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from .schemas import RegisterRequest, UserResponse
from fastapi import HTTPException, status

class UserService:
    
    @staticmethod
    def register_user(db: Session, req: RegisterRequest) -> User:
        """Register a new user"""
        # Check if user exists
        existing = db.query(User).filter(User.email == req.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(
            email=req.email,
            password_hash=hash_password(req.password),
            full_name=req.full_name,
            role=req.role
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        """Get user by ID"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """Get user by email"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    @staticmethod
    def update_user_profile(db: Session, user_id: str, full_name: str = None, role: UserRole = None) -> User:
        """Update user profile"""
        user = UserService.get_user_by_id(db, user_id)
        
        if full_name:
            user.full_name = full_name
        if role:
            user.role = role
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def change_password(db: Session, user_id: str, old_password: str, new_password: str) -> User:
        """Change user password"""
        user = UserService.get_user_by_id(db, user_id)
        
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def deactivate_account(db: Session, user_id: str) -> User:
        """Deactivate user account"""
        user = UserService.get_user_by_id(db, user_id)
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

class TokenService:
    
    @staticmethod
    def store_refresh_token(db: Session, user_id: str, token: str, expires_at: datetime) -> RefreshToken:
        """Store refresh token in database"""
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        return refresh_token
    
    @staticmethod
    def verify_refresh_token(db: Session, token: str) -> dict:
        """Verify and decode refresh token"""
        payload = verify_token(token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Check if token exists in database and is not revoked
        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if not db_token or db_token.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or revoked"
            )
        
        # Check expiration
        if db_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        
        return payload
    
    @staticmethod
    def revoke_refresh_token(db: Session, token: str) -> None:
        """Revoke a refresh token"""
        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if db_token:
            db_token.is_revoked = True
            db.commit()
    
    @staticmethod
    def revoke_user_tokens(db: Session, user_id: str) -> None:
        """Revoke all refresh tokens for a user (logout all devices)"""
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        db.commit()