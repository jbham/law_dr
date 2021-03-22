from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Form

from app import crud
from app.api.utils.db import get_db
from app.api.utils.security import get_current_active_user
from app.db_models.user import User as DBUser
from app.models.file import (FileCreationUpdateFinalResponse, FileUpdateReturnResponse, FileUpdateRequestModel,
                             DownloadFileS3Dest, FileDelete)
from app.crud.file import get_mention_by_mention_id, prepare_download_file, get_bucket_location_by_file_and_file_state_id
from app.api.api_logging import logger
from app.crud.case import confirm_case_id_with_biz_id_helper_func
from app.core.config import AWS_UPLOAD_BUCKET
from starlette.responses import Response

router = APIRouter()


@router.post("/file/filepolicy", tags=["file"], response_model=FileCreationUpdateFinalResponse)
def create_file_and_policy(db: Session = Depends(get_db), filename: str = Body(None), newCase: str = Body(None),
                           current_user: DBUser = Depends(get_current_active_user)):
    file = crud.file.create_file_and_get_policy(db, filename, newCase, user_details=current_user)
    return file


@router.put("/file/filepolicy", tags=["file"], response_model=FileUpdateReturnResponse)
def update_file_details_in_db(db: Session = Depends(get_db), file_request: FileUpdateRequestModel = Body(None),
                              current_user: DBUser = Depends(get_current_active_user)):
    file = crud.file.update_file_details_and_initiate_lambda(db, file_request, user_details=current_user)
    return file


# @router.post("/file/", tags=["file"], response_model=CaseObjectResponse)
# def create_user(
#     *,
#     db: Session = Depends(get_db),
#     name: str = Body(None),
#     current_user: DBUser = Depends(get_current_active_user),
# ):
#     """
#     Create new user
#     """
#
#     user = crud.case.get_by_case_number(db, name=name)
#     if user:
#         raise HTTPException(
#             status_code=400,
#             detail="The case with this name already exists in the system.",
#         )
#     try:
#         case_in = Case(business_id=current_user.business_id,
#                        name=name,
#                        created_by=current_user.id,
#                        modified_by=current_user.id)
#
#         user = crud.case.create(db, case_in=case_in)
#
#         return user
#     except Exception as e:
#         print(e)
#         raise HTTPException(
#             status_code=400,
#             detail=str(e),
#         )


@router.get("/file/download", tags=["file"], response_model=DownloadFileS3Dest)
def download_file(*, db: Session = Depends(get_db),
                  case_id: int,
                  current_user: DBUser = Depends(get_current_active_user), response: Response,
                  file_id: Optional[int] = None,
                  file_state_id: Optional[int] = None,
                  fd: Optional[str] = None,
                  ):
    """

    :param response: adds expiration from what we got back from S3's STS
    :param db:
    :param file_id:
    :param file_state_id:
    :param case_id:
    :param fd: This is S3 File destination
    :param current_user:
    :return:
    """
    confirm_case_id_with_biz_id_helper_func(db, case_id, current_user)

    s3_file: str = None

    if file_id:
        res = get_bucket_location_by_file_and_file_state_id(db,
                                                            file_id=file_id,
                                                            file_state_id=file_state_id,
                                                            user_details=current_user)

        s3_file = res.s3_file_dest

    if fd:
        # browser sent us a full S3 file destination. Let's verify that its actually belongs to this user/business
        fd1 = fd.split("/")
        provided_business_id = int(fd1[0])

        # if provided biz id is not the same as user's business id then reject it
        if provided_business_id != current_user.business_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid details passed.",
            )
        provided_case_name = fd1[1]
        provided_split_file_id = str(fd1[2]).split("_")[0]

        res = crud.file.get_filestate_files(db, ids=[provided_split_file_id], user_details=current_user)

        for r in res:
            if r.new_file_name == fd:
                s3_file = r.new_file_name
                break

    if s3_file:
        cred = prepare_download_file(db, s3_file, user_details=current_user)

        # set expiration on client side to 2 minutes less than S3's credentials expiration date
        response.headers[
            "cache-control"] = f"private, max-age={int(80)}"

        return DownloadFileS3Dest(response=cred,
                                  loc=s3_file,
                                  bucket=AWS_UPLOAD_BUCKET)
    else:
        return DownloadFileS3Dest(response={},
                                  loc="",
                                  bucket="")


@router.post("/file/delete", tags=["file"], response_model=FileDelete)
def delete_file(*, db: Session = Depends(get_db), file_id: list = Body(None),
                current_user: DBUser = Depends(get_current_active_user)):
    f_id = [(int(i["id"]),) for i in file_id if "id" in i]

    # confirm_file_for_user = crud.file.get_by_file_ids(db, ids=f_id, user_details=current_user)

    try:
        result = crud.file.get_filestate_files(db, ids=f_id, user_details=current_user)

        # extract unique and all s3 files to delete
        s3_files_delete = ()
        for r in result:
            s3_files_delete = s3_files_delete + r
        final_s3_files_delete = list(set(s3_files_delete))

        # delete from database first
        crud.file.delete_by_file_id(db, file_id=f_id, user_details=current_user)

        # delete from s3 next
        crud.file.delete_s3_file(final_s3_files_delete)

    except Exception as e:
        logger.info(f'Exception occurred while deleting file with id: {file_id} for '
                    f"business_id: {current_user.business_id}. Exception is: ")
        logger.info(e)
        raise HTTPException(
            status_code=400,
            detail="There was a problem while deleting file.",
        )

    return FileDelete(response="success")
