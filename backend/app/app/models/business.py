from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# Shared properties
class BusinessBase(BaseModel):
    full_name: str = None
    main_administrator: EmailStr = None
    licenses_to_purchase: int = 0
    is_active: Optional[bool] = True
    created_by: int = None
    created_date: datetime = None
    modified_date: datetime = None
    modified_by: int = None
    id: int = None

    class Config:
        orm_mode = True


class Business(BusinessBase):
    pass


class BusinessUserPool(BusinessBase):
    user_pool_id: str = None
    user_pool_name: str = None
    user_pool_arn: str = None
    user_pool_created_date: datetime = None
    user_pool_modified_date: datetime = None

    class Config:
        orm_mode = True


