from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Any


# Shared properties
class FileBase(BaseModel):
    business_id: int = None
    name: str = None
    created_by: int = None
    created_date: datetime = None
    modified_date: datetime = None
    modified_by: int = None
    id: int = None


class InitialFileCreation( BaseModel ):
    business_id: int = None
    name: str = None
    created_by: int = None
    modified_by: int = None
    case_id: int = None

    class Config:
        orm_mode = True


class FileObjectInitialCreationResponse(InitialFileCreation):
    id: int = None
    path: str = None

    class Config:
        orm_mode = True


class FileCreationUpdateFinalResponse(BaseModel):
    response: dict = None
    file_name: str = None
    url: str = None
    file_id: int = None

    class Config:
        orm_mode = True


class FileUpdateReturnResponse(BaseModel):
    id: int = None
    saved: bool = None

    class Config:
        orm_mode = True


class FileUpdateRequestModel(BaseModel):
    fileId: int = None
    fileType: str = None
    fileSize: int = None
    httpStatusCode: str = None
    httpStatusMessage: str = None
    response:  str = None
    splitFile:  bool = True
    splitFileTerm: str = None

    class Config:
        orm_mode = True


class DownloadFileS3Dest(BaseModel):
    response: dict = None
    loc: str = None
    bucket: str = None

    # class Config:
    #     orm_mode = True


class FileDelete(BaseModel):
    response: str = None


class ShowMePDF(BaseModel):

    id: str = None
    name: str = None

    class Config:
        orm_mode = True




