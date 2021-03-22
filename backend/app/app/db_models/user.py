import datetime

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base
from app.db_models.business import Business


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id"), nullable=False)
    # full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    # hashed_password = Column(String)
    is_active = Column(Boolean(), default=True)
    is_main_admin = Column(Boolean(), default=False)
    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    modified_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                           nullable=False)
    cognito_user_id = Column(String)
    modified_by = Column(Integer, ForeignKey('user.id'), nullable=False)

    created_by_user = relationship("User", backref=backref('user_created_by', remote_side=[id]),
                                   foreign_keys=[created_by])
    modified_by_user = relationship("User", backref=backref('user_modified_by', remote_side=[id]),
                                    foreign_keys=[modified_by])
