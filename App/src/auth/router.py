from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from auth.schemas import UserRegister,UserPrivate
from auth.models import User
from auth.database import get_session
from auth.security import hash_password, verify_password, create_access_token
from config import BASE_DIR
from .deps import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
import json


templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "templates"))

router = APIRouter(prefix="/auth", tags=["auth"])



@router.get('/login')
def login(request: Request):
    return templates.TemplateResponse(request= request, name = 'login.html')


@router.get('/register')
def login(request: Request):
    return templates.TemplateResponse(request= request, name = 'register.html')



#REGISTER

@router.post('/register', status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, session: Session = Depends(get_session)):
    existing = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()    


    if existing: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email deja inregistrat"
        )
    

    user = User(
        nume = user_data.nume,
        email = user_data.email,
        hashed_password = hash_password(user_data.password)
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "message": "Cont creat cu succes!",
        "user_id": user.id        
    }


#LOGIN

@router.post('/login', status_code=status.HTTP_200_OK)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email sau parolă incorectă"
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email sau parolă incorectă"
        )
    

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


#ACCESS CURRENT USER


@router.get('/me', response_model=UserPrivate)
def get_current_user_endpoint(current_user: User = Depends(get_current_user)):
    return current_user




@router.get("/history")
def get_user_history(current_user: User = Depends(get_current_user)):

    from .models import ScanHistory
    from .database import get_session_direct    

    session = get_session_direct()

    scans = session.exec(
        select(ScanHistory)
        .where(ScanHistory.user_id == current_user.id).order_by(ScanHistory.created_at.desc())
    ).all()


    result = []

    for scan in scans:
        result.append(
            {
            "id": scan.id,
            "image_url": scan.image_url,
            "summary": json.loads(scan.summary_json),
            "ingredients": json.loads(scan.ingredients_json),
            "created_at": scan.created_at.strftime("%d.%m.%Y %H:%M")
            }
        )

    session.close()
    return result    