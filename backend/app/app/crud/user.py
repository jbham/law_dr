import boto3
import hmac
import hashlib
import base64

from typing import List, Optional
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from app.core.security import get_password_hash, verify_password
from app.db_models.user import User
from app.db_models.business import Business
from app.models.token import Token
from app.models.user import UserInCreate, UserInUpdate, UserLogin, UserWithNewPassword


class Cognito:

    def __init__(self, client_id=None, user_pool_id=None, user_pool_client_secret: bytes = None, region=None):
        self.client_id = client_id
        self.user_pool_id = user_pool_id
        self.client_secret = user_pool_client_secret
        self.region = region
        self.client = boto3.client('cognito-idp', region_name=self.region)

    def get_secret_hash(self, username):
        # A keyed-hash message authentication code (HMAC) calculated using
        # the secret key of a user pool client and username plus the client
        # ID in the message.

        message = username + self.client_id
        dig = hmac.new(self.client_secret, msg=message.encode('UTF-8'),
                       digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    def authenticate(self, user_to_auth: UserLogin) -> Optional[Token]:

        try:
            response = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,  # "2lmkmdeqbtrc04rndthiflofhi",
                AuthFlow="ADMIN_NO_SRP_AUTH",
                AuthParameters={
                    'USERNAME': user_to_auth.email,
                    'PASSWORD': user_to_auth.password,
                    'SECRET_HASH': self.get_secret_hash(user_to_auth.email)
                },
            )

            if "ChallengeName" in response:
                if response["ChallengeName"] == "NEW_PASSWORD_REQUIRED":
                    obj = Token(message="NEW_PASSWORD_REQUIRED",
                                session=response["Session"])
                    return obj

        except Exception as e:
            print(e.response["Error"]["Message"])
            raise HTTPException(status_code=e.response["ResponseMetadata"]["HTTPStatusCode"],
                                detail="Unable to process this request.")

        return response["AuthenticationResult"]  # this is of type Token

    def response_to_challenge(self, challenge, user_with_new_password: UserWithNewPassword):
        if challenge == "NEW_PASSWORD_REQUIRED":
            # client = boto3.client('cognito-idp')
            response = self.client.admin_respond_to_auth_challenge(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                ChallengeResponses={
                    "USERNAME": user_with_new_password.email,
                    "NEW_PASSWORD": user_with_new_password.new_password,
                    "SECRET_HASH": self.get_secret_hash(user_with_new_password.email)
                },
                Session=user_with_new_password.session_str,
                # AnalyticsMetadata={
                #     'AnalyticsEndpointId': 'string'
                # },
                # ContextData={
                #     'IpAddress': 'string',
                #     'ServerName': 'string',
                #     'ServerPath': 'string',
                #     'HttpHeaders': [
                #         {
                #             'headerName': 'string',
                #             'headerValue': 'string'
                #         },
                #     ],
                #     'EncodedData': 'string'
                # }
            )
            return response


def get(db_session, *, cognito_user_id: str) -> Optional[User]:
    return db_session.query(User).filter(User.cognito_user_id == cognito_user_id).first()


def get_by_email(db_session, *, email: str) -> Optional[User]:
    return db_session.query(User).filter(User.email == email).first()


def get_secret_hash(username):
    # A keyed-hash message authentication code (HMAC) calculated using
    # the secret key of a user pool client and username plus the client
    # ID in the message.

    client_secret = b"8d15hdqvl26p9sdh4k5l93h5cs9gh91c0n3i2eruj8c0ms7h5as"
    message = username + "2lmkmdeqbtrc04rndthiflofhi"
    dig = hmac.new(client_secret, msg=message.encode('UTF-8'),
                   digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def authenticate(user_to_auth: UserLogin) -> Optional[Token]:
    # user = get_by_email(db_session, email=email)
    # if not user:
    #     return None
    # if not verify_password(password, user.hashed_password):
    #     return None
    # return user

    # client_id = get_user_business(db_session, user_to_auth.email)

    try:
        # client = boto3.client('cognito-idp')
        response = client.admin_initiate_auth(
            UserPoolId=user_to_auth.user_pool_id,
            ClientId="2lmkmdeqbtrc04rndthiflofhi",
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={
                'USERNAME': user_to_auth.email,
                'PASSWORD': user_to_auth.password,
                'SECRET_HASH': get_secret_hash(user_to_auth.email)
            },

        )
    except Exception as e:
        return e.response["Error"]["Message"]

    return response["AuthenticationResult"]


def response_to_challenge(challenge, user_with_new_password: UserLogin):
    if challenge == "NEW_PASSWORD_REQUIRED":
        # client = boto3.client('cognito-idp')
        response = client.admin_respond_to_auth_challenge(
            UserPoolId=user_with_new_password.user_pool_id,
            ClientId="2lmkmdeqbtrc04rndthiflofhi",
            ChallengeName='NEW_PASSWORD_REQUIRED',
            ChallengeResponses={
                "USERNAME": user_with_new_password.email,
                "NEW_PASSWORD": user_with_new_password.password,
                "SECRET_HASH": get_secret_hash(user_with_new_password.email)
            },
            Session=user_with_new_password.session_str,
            # AnalyticsMetadata={
            #     'AnalyticsEndpointId': 'string'
            # },
            # ContextData={
            #     'IpAddress': 'string',
            #     'ServerName': 'string',
            #     'ServerPath': 'string',
            #     'HttpHeaders': [
            #         {
            #             'headerName': 'string',
            #             'headerValue': 'string'
            #         },
            #     ],
            #     'EncodedData': 'string'
            # }
        )
        return response


def is_active(user) -> bool:
    return user.is_active


def is_superuser(user) -> bool:
    return user.is_superuser


def get_multi(db_session, *, skip=0, limit=100, user_details=None) -> List[Optional[User]]:
    return db_session.query(User).filter_by(business_id=user_details.business_id).offset(skip).limit(limit).all()


def get_user_business(db_session, current_user):
    return db_session.query(Business).join(User, User.business_id == Business.id) \
        .filter(User.email == current_user).all()


def create_user_in_cognito(db_session, user_to_create: str, current_user=None, user_pool_id=None):
    if user_to_create is None:
        raise HTTPException(
            status_code=400,
            detail="Not all details were supplied to create a user.",
        )

    if user_pool_id is None:
        if current_user is None:
            raise HTTPException(
                status_code=400,
                detail="Not all details were supplied to create a user.",
            )
        user_business: Business = get_user_business(db_session, user_to_create)
        user_pool_id = user_business.user_pool_id

    # client = boto3.client('cognito-idp')
    response = client.admin_create_user(
        UserPoolId=user_pool_id,
        Username=user_to_create,
        # UserAttributes=[
        #     {
        #         'Name': 'string',
        #         'Value': 'string'
        #     },
        # ],
        # ValidationData=[
        #     {
        #         'Name': 'string',
        #         'Value': 'string'
        #     },
        # ],
        # TemporaryPassword='string',
        # ForceAliasCreation=True | False,
        # MessageAction='RESEND' | 'SUPPRESS',
        DesiredDeliveryMediums=[
            'EMAIL',
        ]
    )


def create_main_admin(db_session, user_to_create=None, current_user=None, pool_id=None):
    create_user_in_cognito(db_session, user_to_create=user_to_create, current_user=current_user, user_pool_id=pool_id)


def create(db_session, *, user_in: UserInCreate) -> User:
    create_user_in_cognito(db_session, user_to_create=user_in.email, user_pool_id=None)
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_superuser=user_in.is_superuser,
        business_id=user_in.business_id,
        created_by=user_in.created_by,
        modified_by=user_in.modified_by,
        is_active=user_in.is_active
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def update(db_session, *, user: User, user_in: UserInUpdate) -> User:
    user_data = jsonable_encoder(user)
    for field in user_data:
        if field in user_in.fields:
            value_in = getattr(user_in, field)
            if value_in is not None:
                setattr(user, field, value_in)
    if user_in.password:
        passwordhash = get_password_hash(user_in.password)
        user.hashed_password = passwordhash
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
