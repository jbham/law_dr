from typing import List, Optional

from sqlalchemy import and_, func, case
from fastapi import HTTPException

from app.db_models.case import Case as DBCase
from app.db_models.ctakes_mentions import CtakesMentions as DBCtakesMentions
from app.db_models.file import File as DBFile
from app.db_models.file import FileState as DBFileState
from app.db_models.user import User
from app.models.case import Case, CaseObjectResponse, AllCaseFiles
from app.api.api_logging import logger


def get_multi(db_session, *, skip=0, limit=100, user_details=None) -> List[Optional[DBCase]]:
    return db_session.query(DBCase).filter_by(business_id=user_details.business_id).offset(skip).limit(limit).all()


def get_by_case_number(db_session, *, name: str, user_details=None) -> Optional[DBCase]:
    return db_session.query(DBCase) \
        .filter(DBCase.name == name) \
        .filter(DBCase.business_id == user_details.business_id) \
        .first()


def get_by_case_id(db_session, *, id: int, user_details=None) -> Optional[DBCase]:
    return db_session.query(DBCase) \
        .filter(DBCase.id == id) \
        .filter(DBCase.business_id == user_details.business_id) \
        .first()


def create(db_session, *, case_in: Case) -> CaseObjectResponse:
    case = DBCase(
        name=case_in.name,
        business_id=case_in.business_id,
        created_by=case_in.created_by,
        modified_by=case_in.modified_by,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def confirm_case_id_with_biz_id_helper_func(db, case_id, current_user):
    confirm_case_id_with_biz_id = get_by_case_id(db, id=case_id, user_details=current_user)

    if not confirm_case_id_with_biz_id:
        logger.info(f"Invalid case_id of value {case_id} found for business_id {current_user.business_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid details passed.",
        )


# def fetch_mentions_by_id(db_session, *, case_id: int, user_details=None) -> Optional[CaseMentionResponse]:
#     resp = db_session.query(DBCtakesMentions.id,
#                             DBCtakesMentions.business_id,
#                             DBCtakesMentions.text,
#                             DBCtakesMentions.page_num,
#                             DBCtakesMentions.ctakes_cas,
#                             DBCtakesMentions.visit_date,
#                             DBCtakesMentions.user_id,
#                             DBCtakesMentions.created_by,
#                             DBCtakesMentions.modified_by,
#                             DBCtakesMentions.created_date,
#                             DBCtakesMentions.modified_date) \
#         .join(DBFile, and_(DBFile.id == DBCtakesMentions.file_id,
#                            DBFile.business_id == DBCtakesMentions.business_id)) \
#         .join(DBCase, and_(DBCase.id == DBFile.case_id,
#                            DBCase.business_id == DBFile.business_id)) \
#         .filter(DBCtakesMentions.business_id == user_details.business_id,
#                 DBCase.id == case_id,
#                 DBCtakesMentions.overlapping_entry == None) \
#         .all()
#
#     return resp


def get_all_case_files(db_session, *, this_case_id: int, user_details=None) -> Optional[AllCaseFiles]:
    # resp = db_session.query(DBFile.id, User.email.label("user_id"),
    #                         DBFile.modified_date, DBFile.name,
    #                         func.count().label("total_split_files"),
    #                         func.count(case([((DBFileState.splitter_status == 'fail'), 'fail'),
    #                                          ((DBFileState.ctakes_processing_status == 'fail'), 'fail'),
    #                                          ((DBFileState.mentions_processing_status == 'fail'), 'fail')])).label(
    #                             "failed"),
    #                         func.count(case([((DBFileState.splitter_status == 'completed'), 'completed'),
    #                                          ((DBFileState.ctakes_processing_status == 'completed'), 'completed'),
    #                                          ((DBFileState.mentions_processing_status == 'completed'),
    #                                           'completed')])).label(
    #                             "completed")) \
    #     .join(DBFileState, and_(DBFileState.business_id == DBFile.business_id,
    #                             DBFileState.file_id == DBFile.id)) \
    #     .join(User, and_(User.business_id == DBFile.business_id,
    #                      User.id == DBFile.modified_by,
    #                      User.business_id == DBFileState.business_id,
    #                      User.id == DBFileState.last_modified_by)) \
    #     .filter(DBFile.business_id == user_details.business_id,
    #             DBFile.case_id == this_case_id) \
    #     .group_by(DBFile.id, User.email,
    #               DBFile.modified_date, DBFile.name) \
    #     .all()

    resp = db_session.query(DBFile.id, DBFileState.id.label("split_file_id"), DBFile.name, DBFile.size, DBFile.file_type, DBFileState.new_file_name, DBFileState.total_split_pages,
                            DBFileState.splitter_status.label("file_split_status"), DBFileState.ctakes_processing_status.label("file_process_status"),
                            DBFileState.mentions_processing_status.label("terms_extraction_status"))\
        .join(DBFileState, and_(DBFileState.business_id == DBFile.business_id,
                                DBFileState.file_id == DBFile.id))\
        .join(DBCase, and_(DBCase.business_id == DBFile.business_id, DBCase.id == DBFile.case_id))\
        .filter(DBCase.id == this_case_id)\
        .all()
    return resp


def get_files_from_file_state_by_case_id(db_session, *, case_id: int, user_details=None):
    return db_session.query(DBFileState.id,
                            DBFileState.file_id,
                            DBFileState.last_modified_instant,
                            DBFileState.confirmed_visit_date,
                            DBFile.name) \
        .join(DBFile, and_(DBFile.id == DBFileState.file_id,
                           DBFile.business_id == user_details.business_id,
                           DBFileState.business_id == user_details.business_id, )) \
        .filter(DBFile.case_id == case_id) \
        .filter(DBFileState.business_id == user_details.business_id) \
        .filter(DBFileState.confirmed_visit_date != None) \
        .all()
