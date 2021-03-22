from datetime import datetime, timedelta
from typing import List
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app import crud
from app.api.utils.db import get_db
from app.api.utils.security import get_current_user
from app.db_models.user import User as DBUser
from app.models.case import Case, CaseObjectResponse, CaseMentionResponse, AllCaseFiles, CreateCasePayload
from app.api.utils.security import get_current_active_user
from starlette.responses import Response

router = APIRouter()


@router.get("/cases/", tags=["case"], response_model=List[CaseObjectResponse])
def retrieve_all_cases(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: DBUser = Depends(get_current_user),
):
    """
    Retrieve business as super user
    """
    case = crud.case.get_multi(db, user_details=current_user, skip=skip, limit=limit)
    return case



@router.post("/cases/create/", tags=["case"], response_model=CaseObjectResponse)
def create_case(
        *,
        db: Session = Depends(get_db),
        name: CreateCasePayload,
        current_user: DBUser = Depends(get_current_active_user),
):
    """
    Create new user
    """

    user = crud.case.get_by_case_number(db, name=name.name, user_details=current_user)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The case with this name already exists in the system.",
        )
    try:
        case_in = Case(business_id=current_user.business_id,
                       name=name.name,
                       created_by=current_user.id,
                       modified_by=current_user.id)

        user = crud.case.create(db, case_in=case_in)

        return user
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/cases/{case_id}/searchmentions/", tags=["case"], response_model=List[CaseMentionResponse])
def fetch_mentions(
        *,
        db: Session = Depends(get_db),
        case_id: int,
        current_user: DBUser = Depends(get_current_active_user),
):
    print(case_id)
    resp = crud.case.fetch_mentions_by_id(db, case_id=case_id, user_details=current_user)
    return resp


@router.get("/cases/{case_id}/", tags=["case"], response_model=CaseObjectResponse)
def fetch_mentions(
        *,
        db: Session = Depends(get_db),
        case_id: int,
        current_user: DBUser = Depends(get_current_active_user),
):
    print(case_id)
    case = crud.case.get_by_case_id(db, id=case_id, user_details=current_user)
    return case



@router.get("/cases/{case_id}/files/", tags=["case"], response_model=List[AllCaseFiles])
def fetch_case_files(
        *,
        db: Session = Depends(get_db),
        case_id: int,
        current_user: DBUser = Depends(get_current_active_user),
        response: Response
):
    print(case_id)
    resp = crud.case.get_all_case_files(db, this_case_id=case_id, user_details=current_user)
    # response.headers["cache-control"] = f"private, max-age={int(86400)}"

    return resp
