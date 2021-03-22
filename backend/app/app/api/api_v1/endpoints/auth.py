from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import  OAuth2PasswordRequestForm

from app.models.token import Token
from sqlalchemy.orm import Session
from app.api.utils.db import get_db
from app import crud
from app.models.user import User, UserLogin, UserWithNewPassword

router = APIRouter()


@router.post("/auth/login", response_model=Token, tags=["auth"])
def login_access_token_auth(
        db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user_biz = crud.user.get_user_business(db, form_data.username)

    if len(user_biz) > 1:
        HTTPException(status_code=401, detail="Too many details found.")

    if not user_biz:
        HTTPException(status_code=400, detail="Not found")

    user_pool_id = user_biz[0].user_pool_id
    user_pool_arn = user_biz[0].user_pool_arn
    client_id = user_biz[0].user_pool_client
    client_secret = user_biz[0].user_pool_client_secret
    region = user_biz[0].aws_region

    user_in = UserLogin(email=form_data.username,
                        password=form_data.password,
                        user_pool_id=user_pool_id)

    cognito = crud.user.Cognito(client_id=client_id, user_pool_id=user_pool_id, user_pool_client_secret=client_secret,
                                region=region)

    token = cognito.authenticate(user_to_auth=user_in)

    return token


@router.post("/auth/newpassword", response_model=Token, tags=["auth"])
def select_new_password(db: Session = Depends(get_db), username: str = Body(None), temp_password: str = Body(None),
                        new_password: str = Body(None)):
    user_biz = crud.user.get_user_business(db, username)

    if len(user_biz) > 1:
        HTTPException(status_code=401, detail="Too many details found.")

    if not user_biz:
        HTTPException(status_code=400, detail="Not found")

    user_pool_id = user_biz[0].user_pool_id
    user_pool_arn = user_biz[0].user_pool_arn
    client_id = user_biz[0].user_pool_client
    client_secret = user_biz[0].user_pool_client_secret
    region = user_biz[0].aws_region

    user_in = UserLogin(email=username,
                        password=temp_password)

    cognito = crud.user.Cognito(client_id=client_id, user_pool_id=user_pool_id, user_pool_client_secret=client_secret,
                                region=region)

    user = cognito.authenticate(user_to_auth=user_in)

    user_selctd_pw = UserWithNewPassword(email=username,
                                         old_password=temp_password,
                                         new_password=new_password,
                                         session_str=user.session)

    if user.message == "NEW_PASSWORD_REQUIRED":
        cognito.response_to_challenge("NEW_PASSWORD_REQUIRED", user_selctd_pw)
