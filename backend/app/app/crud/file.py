from typing import List, Dict
import sys
import traceback
import os
import json
import boto3
from fastapi import HTTPException
from typing import Optional
from app.api.api_logging import logger
from app.core.config import (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
                             AWS_UPLOAD_BUCKET, AWS_UPLOAD_REGION, AWS_ROLE_ARN,
                             AWS_ROLE_SESSION_NAME, AWS_FULL_DOC_SPLITTER_LAMBDA,
                             AWS_IP, AWS_SQS_Q_NAME)
from app.db_models.file import File, FileState
from app.db_models.ctakes_mentions import CtakesMentions
from app.models.file import (InitialFileCreation, FileObjectInitialCreationResponse,
                             FileCreationUpdateFinalResponse, FileUpdateReturnResponse,
                             FileUpdateRequestModel)
from .case import get_by_case_number
from sqlalchemy.sql import select
from sqlalchemy import tuple_, and_


def get_by_file_ids(db_session, *, ids: list, user_details=None) -> Optional[File]:
    return db_session.query(File) \
        .filter(File.id.in_(ids)) \
        .filter(File.business_id == user_details.business_id) \
        .first()


def get_filestate_files(db_session, *, ids: list, user_details=None):
    """

    :param db_session:
    :param ids:
    :param user_details:
    :return: returns all of the S3 files keys which needs to be deleted, i.e.,
                file.path, file_state.new_file_name, file_state.extract_file_name, file_state.ctakes_json_file_name
    """

    return db_session.query(File.path, FileState.new_file_name,
                            FileState.extract_file_name, FileState.ctakes_json_file_name). \
        join(File, and_(File.id == FileState.file_id,
                        File.business_id == FileState.business_id,
                        File.business_id == user_details.business_id,
                        FileState.business_id == user_details.business_id)). \
        filter(FileState.file_id.in_(ids)).all()


def delete_by_file_id(db_session, *, file_id: list, user_details=None):
    # this is a cascade delete. It will delete from following tables:
    #   select * from file;
    #   select * from file_state;
    #   select * from sf_ctakes_mentions;
    #   select * from mentions_rel_text;
    try:
        deleted_objects = File.__table__.delete().where(File.id.in_(file_id))
        db_session.execute(deleted_objects)
        db_session.commit()
    except Exception as e:
        logger.info(f"Exception for business_id: {user_details.business_id} and user: {user_details.id} "
                    f"{e}")
        traceback.print_exc(file=sys.stdout)
        raise HTTPException(
            status_code=400,
            detail="Exception occurred while deleting file(s).",
        )

    return True


def delete_s3_file(file_to_delete, user_details=None):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    delete_objects = [{'Key': str(i)} for i in file_to_delete]
    try:
        response = s3.delete_objects(
            Bucket=AWS_UPLOAD_BUCKET,
            Delete={
                'Objects': delete_objects
            }
        )
    except Exception as e:
        print(e.response['Error'])
        print(
            f"Error occurred while assuming role for business_id: {user_details.business_id} "
            f"and user: {user_details.id} and exception is as follows: \n {e}")
        traceback.print_exc(file=sys.stdout)
        raise HTTPException(
            status_code=400,
            detail=e.response['Error'],
        )


def get_mention_by_mention_id(db_session, *, mention_id: int,
                              user_details=None) -> Optional[CtakesMentions]:
    return db_session.query(CtakesMentions) \
        .filter(CtakesMentions.id == mention_id) \
        .filter(CtakesMentions.business_id == user_details.business_id) \
        .first()

def get_bucket_location_by_file_and_file_state_id(db_session, *, file_id: int, file_state_id: int, user_details=None) -> Optional[CtakesMentions]:
    return db_session.query(CtakesMentions)\
        .distinct(CtakesMentions.s3_file_dest, CtakesMentions.bucket)\
        .filter(CtakesMentions.file_id == file_id) \
        .filter(CtakesMentions.file_state_id == file_state_id) \
        .filter(CtakesMentions.business_id == user_details.business_id) \
        .first()


def create_file_and_get_policy(db_session, filename, newCase, user_details=None) -> FileCreationUpdateFinalResponse:
    db_case = get_by_case_number(db_session, name=newCase, user_details=user_details)

    if not db_case:
        raise HTTPException(
            status_code=400,
            detail="This case does not exist in the system",
        )

    file = InitialFileCreation(business_id=user_details.business_id,
                               name=filename,
                               created_by=user_details.id,
                               modified_by=user_details.id,
                               case_id=db_case.id)

    created_file = create_file(db_session, file_in=file)

    file_obj_id = created_file.id
    upload_start_path = f"{user_details.business_id}/{db_case.name}/"
    _, file_extension = os.path.splitext(filename)
    filename_final = f"{file_obj_id}{file_extension}"
    final_upload_path = f"{upload_start_path}{filename_final}"

    url = 'https://{bucket}.s3-{region}.amazonaws.com/'.format(
        bucket=AWS_UPLOAD_BUCKET,
        region=AWS_UPLOAD_REGION
    )

    if filename and file_extension:
        created_file.path = final_upload_path
        update_created_file_details_in_db(db_session, file_in=created_file)

    myBucketPolicy = f"""{{
                "Version": "2012-10-17",
                "Statement": [
                    {{
                        "Sid": "StarfizzUploadPolicy",
                        "Effect": "Allow",
                        "Action": [
                            "s3:PutObject"
                        ],
                        "Resource": [
                            "arn:aws:s3:::{AWS_UPLOAD_BUCKET}/{user_details.business_id}/{db_case.name}/*"
                        ],
                        "Condition": {{
                             "IpAddress": {{"aws:SourceIp": "{AWS_IP}"}}
                        }} 
                    }}
                ]
            }}"""

    client = boto3.client('sts', aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    try:
        response = client.assume_role(RoleArn=AWS_ROLE_ARN,
                                      RoleSessionName=AWS_ROLE_SESSION_NAME,
                                      Policy=myBucketPolicy,
                                      DurationSeconds=900)

        print(
            f"business_id: {user_details.business_id} and user: {user_details.id} assumed role to upload file {filename}"
            f"and exception is as follows: \n {response}")

    except Exception as e:
        print(e.response['Error'])
        print(
            f"Error occurred while assuming role for business_id: {user_details.business_id} and user: {user_details.id} "
            f"and exception is as follows: \n {e}")
        raise HTTPException(
            status_code=400,
            detail=e.response['Error'],
        )

    res = FileCreationUpdateFinalResponse(response=response["Credentials"],
                                          file_name=final_upload_path,
                                          url=url,
                                          file_id=file_obj_id)

    return res


def update_created_file_details_in_db(db_session, *, file_in: FileObjectInitialCreationResponse) -> \
        FileObjectInitialCreationResponse:
    file_to_update = file_in
    db_session.add(file_to_update)
    db_session.commit()
    db_session.refresh(file_to_update)
    return file_to_update


def create_file(db_session, *, file_in: InitialFileCreation) -> FileObjectInitialCreationResponse:
    case = File(
        name=file_in.name,
        business_id=file_in.business_id,
        created_by=file_in.created_by,
        modified_by=file_in.modified_by,
        case_id=file_in.case_id
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def get_file_by_id(db_session, *, id: int, user_details=None) -> Optional[File]:
    return db_session.query(File) \
        .filter(File.id == id) \
        .filter(File.business_id == user_details.business_id) \
        .first()


def update_file_details_and_initiate_lambda(db_session, data: FileUpdateRequestModel,
                                            user_details=None) -> FileUpdateReturnResponse:
    confirmed_file_id = get_file_by_id(db_session, id=data.fileId, user_details=user_details)

    if not confirmed_file_id:
        raise HTTPException(
            status_code=400,
            detail="This file id does not exist in the system",
        )

    path_4_lambda = confirmed_file_id.path

    try:
        db_session.query(File).filter_by(id=data.fileId).update({File.size: data.fileSize,
                                                                 File.uploaded: True if data.response == 'success' else False,
                                                                 File.file_type: data.fileType,
                                                                 File.s3StatusCode: data.httpStatusCode,
                                                                 File.s3StatusMessage: data.httpStatusMessage,
                                                                 File.s3response: data.response})
        db_session.commit()

        if data.response == 'success':

            event = {"business_id": str(user_details.business_id),
                     "user_id": str(user_details.id),
                     "file_item_id": str(data.fileId),
                     "s3_location": str(path_4_lambda),
                     "splitFileTerm": data.splitFileTerm,
                     "aws_access_key_id": AWS_ACCESS_KEY_ID,
                     "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
                     "bucket": AWS_UPLOAD_BUCKET,
                     "sqs_q_name": AWS_SQS_Q_NAME}

            # if splitting file is required
            if data.splitFile:
                return initiate_splitter_lambda(confirmed_file_id.id, event)

            # else go straight to extract text
            elif not data.splitFile:

                # TODO (adding logic to initiate lambda for extracting text here)
                pass

        else:
            return FileUpdateReturnResponse(id=confirmed_file_id.id,
                                            saved=False)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


def initiate_splitter_lambda(file_id: int, event) -> FileUpdateReturnResponse:
    try:
        lambda_client = boto3.client('lambda',
                                     aws_access_key_id=AWS_ACCESS_KEY_ID,
                                     aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

        res = lambda_client.invoke(FunctionName=AWS_FULL_DOC_SPLITTER_LAMBDA,
                                   InvocationType='Event',
                                   Payload=json.dumps(event))

        return FileUpdateReturnResponse(id=file_id,
                                        saved=True)

    except Exception as e:
        print(e)
        return FileUpdateReturnResponse(id=file_id,
                                        saved=False)


def prepare_download_file(db_session, file_dest, user_details=None):
    myBucketPolicy = f"""{{
                    "Version": "2012-10-17",
                    "Statement": [
                        {{
                            "Sid": "StarfizzUploadPolicy",
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObject"
                            ],
                            "Resource": [
                                "arn:aws:s3:::{AWS_UPLOAD_BUCKET}/{file_dest}"
                            ],
                            "Condition": {{
                                 "IpAddress": {{"aws:SourceIp": "{AWS_IP}"}}
                            }} 
                        }}
                    ]}}"""

    client = boto3.client('sts', aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    try:
        response = client.assume_role(RoleArn=AWS_ROLE_ARN,
                                      RoleSessionName=AWS_ROLE_SESSION_NAME,
                                      Policy=myBucketPolicy,
                                      DurationSeconds=900)

        print(
            f"business_id: {user_details.business_id} and user: {user_details.id} assumed role to download file "
            f"{file_dest} and response is as follows: \n {response}")

    except Exception as e:
        print(e.response['Error'])
        print(
            f"Error occurred while assuming role for business_id: {user_details.business_id} and user: {user_details.id} "
            f"and exception is as follows: \n {e}")
        raise HTTPException(
            status_code=400,
            detail=e.response['Error'],
        )

    response["Credentials"]["region"] = AWS_UPLOAD_REGION
    return response["Credentials"]
