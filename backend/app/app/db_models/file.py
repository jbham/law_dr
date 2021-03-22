import datetime
import enum
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, TIMESTAMP, BigInteger, SMALLINT, Enum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class File(Base):
    __tablename__ = "file"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id"), nullable=False)
    name = Column(String)
    path = Column(String)
    size = Column(BigInteger)
    file_type = Column(String)
    uploaded = Column(String)
    active = Column(String)
    case_id = Column(Integer, ForeignKey("case.id"), nullable=False)
    s3StatusCode = Column(SMALLINT)
    s3StatusMessage = Column(String)
    s3response = Column(String(25))

    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    modified_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                           nullable=False)
    modified_by = Column(Integer, ForeignKey('user.id'), nullable=False)

    file_created_by = relationship("User", foreign_keys=[created_by])
    file_modified_by = relationship("User", foreign_keys=[modified_by])
    file_business_id = relationship("Business", foreign_keys=[business_id])
    file_case_id = relationship("Case", foreign_keys=[case_id])


class FileStateEnum(enum.Enum):
    created = 0
    running = 1
    completed = 2
    fail = 3

# some examples of SQLALCHEMY usage
# https://gist.github.com/matin/736945/f3f87342e25000371c711bd8624b43b4e07611a3


class FileState(Base):
    __tablename__ = "file_state"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("file.id", ondelete='CASCADE'), nullable=False)
    new_file_name = Column(String)

    last_modified_by = Column(Integer, ForeignKey('user.id'))
    last_modified_instant = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                                   nullable=False)

    splitter_start_instant = Column(TIMESTAMP)
    splitter_completed_instant = Column(TIMESTAMP)
    splitter_status = Column(Enum(FileStateEnum))
    splitter_s3_upload_resp = Column(String)
    splitter_user_id = Column(Integer, ForeignKey('user.id'))
    splitter_to_extract_text_hand_off_resp = Column(String)
    splitter_generic_exception = Column(String)
    total_split_pages = Column(Integer)

    extract_text_s3_upload_resp = Column(String)
    extract_file_name = Column(String)

    ctakes_start_instant = Column(TIMESTAMP)
    ctakes_json_file_name = Column(String)
    ctakes_processing_status = Column(Enum(FileStateEnum))
    ctakes_user_id = Column(Integer, ForeignKey('user.id'))
    ctakes_completed_instant = Column(TIMESTAMP)
    ctakes_error_response = Column(String)

    mentions_start_instant = Column(TIMESTAMP)
    mentions_processing_status = Column(Enum(FileStateEnum))
    mentions_user_id = Column(Integer, ForeignKey('user.id'))
    mentions_completed_instant = Column(TIMESTAMP)
    mentions_error_response = Column(String)

    ctakes_server_status = Column(String)
    server_name = Column(String)

    filestate_business = relationship("Business", foreign_keys=[business_id])
    filestate_file_id = relationship("File", foreign_keys=[file_id])

    confirmed_visit_date = Column(String)

    splitted_by = relationship("User", foreign_keys=[splitter_user_id])
    ctakes_started_by = relationship("User", foreign_keys=[ctakes_user_id])
    mentions_started_by = relationship("User", foreign_keys=[mentions_user_id])
    last_modified_by_rel = relationship("User", foreign_keys=[last_modified_by])

    # extract_text_start_instant = Column(TIMESTAMP)
    # extract_text_completed_instant = Column(TIME
    #     # ctakes_user_id = Column(Integer, ForeignKey('user.id'))
    #     #
    #     # results_start_instant = Column(TIMESTAMP)
    #     # results_completed_instant = Column(TIMESTAMP)
    #     # results_status = Column(Enum(FileStateEnum))
    #     # results_error = Column(String)
    #     # results_user_id = Column(Integer, ForeignKey('user.id'))
    #     #
    #     filestate_business = relationship("Business", foreign_keys=[business_id])
    #     filestate_file_id = relationship("File", foreign_keys=[file_id])
    #
    #     splitted_by = relationship("User", foreign_keys=[splitter_user_id])
    #     ctakes_processing_by = relationship("User", foreign_keys=[ctakes_user_id])
    #     # text_extracted_by = relationship("User", foreign_keys=[extract_text_user_id])
    #     # ctakes_started_by = relationship("User", foreign_keys=[ctakes_user_id])
    #     # results_started_by = relationship("User", foreign_keys=[results_user_id])
    #     last_modified_by_rel = relationship("User", foreign_keys=[last_modified_by])STAMP)
    # extract_text_status = Column(Enum(FileStateEnum))
    # extract_text_error = Column(String)
    # extract_text_user_id = Column(Integer, ForeignKey('user.id'))
    #
    # ctakes_start_instant = Column(TIMESTAMP)
    # ctakes_completed_instant = Column(TIMESTAMP)
    # ctakes_status = Column(Enum(FileStateEnum))
    # ctakes_error = Column(String)
