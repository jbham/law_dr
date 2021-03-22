import datetime
from sqlalchemy import Boolean, Column, Integer, TIMESTAMP, String
from app.db.base_class import Base


class CTJobLock(Base):
    __tablename__ = "ct_job_lock"

    id = Column(Integer, primary_key=True, index=True)
    checking = Column(Boolean)
    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)
    modified_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                           nullable=False)


class LastBusinessIdProcessed(Base):
    __tablename__ = "last_biz_id_processed"

    id = Column(Integer, primary_key=True)
    last_biz_id = Column(Integer)
    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)
    modified_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                           nullable=False)




