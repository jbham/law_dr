import datetime

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base
from app.db_models.business import Business


class Case(Base):

    __tablename__ = "case"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id"), nullable=False)
    name = Column(String)

    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    modified_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                           nullable=False)
    modified_by = Column(Integer, ForeignKey('user.id'), nullable=False)

    case_created_by = relationship("User", foreign_keys=[created_by])
    case_modified_by = relationship("User", foreign_keys=[modified_by])
    case_business_id = relationship("Business", foreign_keys=[business_id])
