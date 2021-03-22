import json
import time
import urllib.request

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from jose import jwk, jwt
from jose.utils import base64url_decode
from sqlalchemy.orm import Session

from app import crud
from app.api.utils.db import get_db
from app.core import config
from app.db_models.user import User
from app.api.api_logging import logger

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Cognito:
region = config.AWS_UPLOAD_REGION
userpool_id = config.AWS_USER_POOL_ID
app_client_id = config.AWS_USER_POOL_CLIENT_ID
keys_url = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(region, userpool_id)
print(keys_url)
print(region, userpool_id, app_client_id)
# instead of re-downloading the public keys every time
# we download them only on cold start
# https://aws.amazon.com/blogs/compute/container-reuse-in-lambda/

with urllib.request.urlopen(keys_url) as url:
    keys = json.loads(url.read())['keys']


def get_current_user(db: Session = Depends(get_db), token: str = Security(reusable_oauth2)):

    # try:
    #     payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
    #     token_data = TokenPayload(**payload)
    # except PyJWTError:
    #     raise HTTPException(
    #         status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    #     )
    # user = crud.user.get(db, user_id=token_data.user_id)
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return user

    # get the kid from the headers prior to verification
    headers = jwt.get_unverified_headers(token)
    kid = headers['kid']
    # search for the kid in the downloaded public keys
    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    if key_index == -1:
        logger.info('Public key not found in jwks.json')
        return False
    # construct the public key
    public_key = jwk.construct(keys[key_index])
    # get the last two sections of the token,
    # message and signature (encoded in base64)
    message, encoded_signature = str(token).rsplit('.', 1)
    # decode the signature
    decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
    # verify the signature
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        logger.info('Signature verification failed')
        return False
    logger.info('Signature successfully verified')
    # since we passed the verification, we can now safely
    # use the unverified claims
    claims = jwt.get_unverified_claims(token)
    # additionally we can verify the token expiration
    if time.time() > claims['exp']:
        logger.info('Token is expired')
        raise HTTPException(status_code=404, detail="Sessions has expired.")
    # and the Audience  (use claims['client_id'] if verifying an access token)
    if claims['client_id'] != app_client_id:
        logger.info('Token was not issued for this audience')
        raise HTTPException(status_code=404, detail="Unauthorized access. Access denied")
    # now we can use the claims
    # print(claims)

    user = crud.user.get(db, cognito_user_id=claims["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_current_active_user(current_user: User = Security(get_current_user)):
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(current_user: User = Security(get_current_user)):
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user
