from typing import Optional, Dict, Any

from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    email: EmailStr = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    business_id: int
    created_by: int = None
    modified_by: int = None

    class Config:
        orm_mode = True


class UserBaseInDB(UserBase):
    id: int = None

    class Config:
        orm_mode = True


# Properties to receive via API on creation
class UserInCreate(UserBaseInDB):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    class Config:
        orm_mode = True


# Properties to receive via API on update
class UserInUpdate(UserBaseInDB):
    password: Optional[str] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserBaseInDB):
    pass


# Additional properties stored in DB
class UserInDB(UserBaseInDB):
    hashed_password: str


class UserLogin(BaseModel):
    email: EmailStr = None
    password: str = None
    # user_pool_id: str = None
    # session_str: str = Optional[str]


class UserWithNewPassword(BaseModel):
    email: EmailStr = None
    old_password: str = None
    new_password: str = None
    session_str: str = None


class CognitoVerifiedUser(BaseModel):
    pass

