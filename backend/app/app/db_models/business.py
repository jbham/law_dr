import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Business(Base):
    __tablename__ = "business"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    # user_pool_id = Column(String)
    # user_pool_name = Column(String)
    # user_pool_arn = Column(String)
    # user_pool_created_date = Column(DateTime())
    # user_pool_modified_date = Column(DateTime())
    # user_pool_client = Column(String)
    # user_pool_client_secret = Column(BYTEA)
    # aws_region = Column(String)

    created_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('user.id'))
    modified_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    modified_by = Column(Integer, ForeignKey('user.id'))

    # relationships
    created_by_user = relationship("User", foreign_keys=[created_by])
    modified_by_user = relationship("User", foreign_keys=[modified_by])
