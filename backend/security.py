"""
Phase 8: Security, Testing & Deployment
Authentication, RBAC, error handling, and Docker setup
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from models import AuditLog

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token payload"""
    user_id: int
    username: str
    role: str


class User:
    """User model"""
    def __init__(self, id: int, username: str, role: str, is_active: bool = True):
        self.id = id
        self.username = username
        self.role = role
        self.is_active = is_active


class AuthService:
    """Authentication and authorization service"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("user_id")
            username: str = payload.get("username")
            role: str = payload.get("role", "viewer")

            if user_id is None:
                return None

            return TokenData(user_id=user_id, username=username, role=role)
        except JWTError:
            return None


class RBACService:
    """Role-based access control"""

    ROLES = {
        "admin": ["read", "write", "delete", "approve"],
        "officer": ["read", "write", "approve"],
        "viewer": ["read"],
    }

    @staticmethod
    def check_permission(role: str, action: str) -> bool:
        """Check if role has permission for action"""
        permissions = RBACService.ROLES.get(role, [])
        return action in permissions

    @staticmethod
    def require_role(required_roles: list) -> callable:
        """Decorator to require specific roles"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                user = kwargs.get("current_user")
                if not user or user.role not in required_roles:
                    raise PermissionError(f"Role {user.role if user else 'None'} not authorized")
                return func(*args, **kwargs)
            return wrapper
        return decorator


class AuditService:
    """Audit logging service"""

    @staticmethod
    def log_action(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: int,
        user_id: Optional[int] = None,
        details: dict = None,
    ):
        """Log an action to audit trail"""
        try:
            audit_log = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                details=details or {},
            )
            db.add(audit_log)
            db.commit()
            logger.info(f"Audit: {action} on {entity_type} {entity_id} by user {user_id}")
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")

    @staticmethod
    def get_audit_log(db: Session, entity_type: str = None, entity_id: int = None, limit: int = 100) -> list:
        """Retrieve audit logs"""
        query = db.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)

        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()


class ErrorHandler:
    """Standardized error handling"""

    @staticmethod
    def handle_error(error: Exception, context: str = "") -> dict:
        """Convert exception to API error response"""
        logger.error(f"Error in {context}: {str(error)}")

        error_type = type(error).__name__
        return {
            "error": True,
            "type": error_type,
            "message": str(error),
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        }


class HealthCheck:
    """System health check"""

    @staticmethod
    def check_system(db: Session = None) -> dict:
        """Check system health"""
        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "backend": "ok",
                "database": "checking",
                "ocr": "available",
                "llm": "available",
                "embeddings": "available",
            }
        }

        # Check database
        try:
            if db:
                db.execute("SELECT 1")
                status["components"]["database"] = "ok"
        except Exception as e:
            status["components"]["database"] = f"error: {str(e)}"
            status["status"] = "degraded"

        return status


# Demo users (for testing)
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": pwd_context.hash("admin123"),
        "role": "admin",
        "is_active": True,
    },
    "officer": {
        "username": "officer",
        "password_hash": pwd_context.hash("officer123"),
        "role": "officer",
        "is_active": True,
    },
    "viewer": {
        "username": "viewer",
        "password_hash": pwd_context.hash("viewer123"),
        "role": "viewer",
        "is_active": True,
    },
}


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user (demo implementation)"""
    user_data = DEMO_USERS.get(username)
    if not user_data:
        return None

    if not pwd_context.verify(password, user_data["password_hash"]):
        return None

    return User(
        id=hash(username) % 10000,
        username=username,
        role=user_data["role"],
        is_active=user_data["is_active"],
    )
