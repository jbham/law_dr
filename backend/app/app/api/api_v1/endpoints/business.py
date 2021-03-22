from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud
from app.api.utils.db import get_db
from app.api.utils.security import get_current_active_superuser, get_current_active_user
from app.db_models.user import User as DBUser
from app.models.business import Business

router = APIRouter()


@router.get("/business/", tags=["business"], response_model=List[Business])
def retrieve_all_business(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: DBUser = Depends(get_current_active_superuser),
):
    """
    Retrieve business as super user
    """
    business = crud.business.get_multi(db, user_details=current_user, skip=skip, limit=limit)
    return business


@router.post("/business/", tags=["business"], response_model=Business)
def create_business(
        *,
        db: Session = Depends(get_db),
        full_name: str = Body(None),
        main_administrator: EmailStr = Body(None),
        licenses_to_purchase: int = Body(None),
        current_user: DBUser = Depends(get_current_active_user),
):
    business = crud.business.get_by_business_name(db, full_name=full_name)
    if business:
        raise HTTPException(
            status_code=400,
            detail="A business with this name already exists in the system.",
        )

    try:
        business_in = Business(full_name=full_name,
                               licenses_to_purchase=licenses_to_purchase,
                               created_by=current_user.id,
                               modified_by=current_user.id
                               )

        business = crud.business.create(db, main_administrator, business_in=business_in)
        return business
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


