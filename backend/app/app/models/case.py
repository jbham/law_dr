from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import enum
from app.db_models.file import FileStateEnum


# Shared properties
class CaseBase(BaseModel):
    name: str = None
    created_by: int = None
    created_date: datetime = None
    modified_date: datetime = None
    modified_by: int = None
    id: int = None
    business_id: int = None


class Case(CaseBase):
    pass


class CaseObjectResponse(BaseModel):
    id: int = None
    name: str = None
    created_by: int = None
    created_date: datetime = None
    modified_date: datetime = None
    modified_by: int = None

    class Config:
        orm_mode = True


class CaseMentionResponse(BaseModel):
    id: int = None
    business_id: int = None
    text: str = None
    page_num: int = None
    ctakes_cas: str = None
    visit_date: str = None
    user_id: int = None
    created_by: int = None
    modified_by: int = None
    created_date: datetime = None
    modified_date: datetime = None

    class Config:
        orm_mode = True


class CaseSplitFiles(BaseModel):
    pass


class AllCaseFiles(BaseModel):
    # id: int = None
    # user_id : str = None
    # modified_date: datetime = None
    # name: str = None
    # total_split_files : str = None
    # failed: int = None
    # completed: int = None

    id: int = None
    split_file_id: int = None
    name: str = None
    size: int = None
    file_type: str = None
    new_file_name: str = None
    total_split_pages: int = None
    file_split_status: FileStateEnum = None
    file_process_status: FileStateEnum = None
    terms_extraction_status: FileStateEnum = name

    class Config:
        orm_mode = True


class CreateCasePayload(BaseModel):
    name: str
