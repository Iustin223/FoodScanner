from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from .models import User
from .database import get_session
from .security import verify_token


reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(reusable_oauth2), session: Session = Depends(get_session)) -> User:
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token structure"
        )
    
    user = session.exec(
        select(User).where(User.id == int(user_id))
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


reusable_oauth2_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_user_optional(token: str = Depends(reusable_oauth2_optional), session: Session = Depends(get_session)):

    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = session.exec(
        select(User).where(User.id == int(user_id))
    ).first()

    return user