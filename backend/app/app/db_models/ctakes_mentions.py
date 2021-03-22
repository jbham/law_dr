import datetime
from sqlalchemy import (Column, Integer, String, ForeignKey, TIMESTAMP, Float, Table, UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class CtakesMentionsRelText(Base):
    __tablename__ = "mentions_rel_text"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id"), nullable=False, index=True)
    full_text = Column(String)
    full_text_bbox = Column(String)
    file_state_id = Column(Integer, ForeignKey('file_state.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(Integer, ForeignKey('file.id', ondelete='CASCADE'), nullable=False)

    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    modified_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                           nullable=False)
    modified_by = Column(Integer, ForeignKey('user.id'), nullable=False)

    mentions_rel_text_created_by = relationship("User", foreign_keys=[created_by])
    mentions_rel_text_modified_by = relationship("User", foreign_keys=[modified_by])
    mentions_rel_text_business_id = relationship("Business", foreign_keys=[business_id])
    related_rel_text_file_state_id = relationship("FileState", foreign_keys=[file_state_id])
    related_rel_text_file_id = relationship("File", foreign_keys=[file_id])


annotation_relationship = Table(
    'annotation_relationships', Base.metadata,
    # Column('id', Integer, primary_key=True, index=True),
    Column('business_id', Integer, ForeignKey('business.id')),
    Column('annotation_1_id', Integer, ForeignKey('sf_ctakes_mentions.id', ondelete='CASCADE'), index=True, nullable=False),
    Column('annotation_2_id', Integer, ForeignKey('sf_ctakes_mentions.id', ondelete='CASCADE'), index=True, nullable=False),
    UniqueConstraint('annotation_1_id', 'annotation_2_id', name='unique_annot_relationship'),
    # Column('file_state_id', Integer, ForeignKey('file_state.id', ondelete='CASCADE'), nullable=False),
    # Column('file_id', Integer, ForeignKey('file.id', ondelete='CASCADE'), nullable=False),
    # Column('file_id', Integer, ForeignKey('file.id', ondelete='CASCADE'), nullable=False),
    Column('relation_type', String),
    Column('created_date', TIMESTAMP, default=datetime.datetime.utcnow, nullable=False),
    Column('modified_date', TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False))


class CtakesMentions(Base):
    __tablename__ = "sf_ctakes_mentions"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id"), nullable=False, index=True)
    begin = Column(Integer)
    end = Column(Integer)
    text = Column(String)
    # historyOf = Column(Integer)
    # subject = Column(String)
    polarity = Column(Integer)
    confidence = Column(Float)
    # page_num = Column(Integer)
    page_number = Column(Integer)
    annotation_type = Column(String)
    visit_date = Column(String)
    # confirmed_visit_date_by_user = Column(Boolean)
    # match_found = Column(String)
    # test = Column(String)
    # overlapping_entry = Column(Boolean)

    # concept_attributes = Column(JSONB)
    tui = Column(JSONB)
    cui = Column(JSONB)
    rect_coordinates = Column(JSONB)

    body_side = Column(String)
    body_region = Column(JSONB)
    relations = Column(JSONB)

    mention_rel_text_id = Column(Integer, ForeignKey('mentions_rel_text.id', ondelete='CASCADE'), nullable=False,
                                 index=True)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)

    created_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    modified_date = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                           nullable=False)
    modified_by = Column(Integer, ForeignKey('user.id'), nullable=False)

    bucket = Column(String)
    s3_file_dest = Column(String)
    file_state_id = Column(Integer, ForeignKey('file_state.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(Integer, ForeignKey('file.id', ondelete='CASCADE'), nullable=False)

    mentions_created_by = relationship("User", foreign_keys=[created_by])
    mentions_modified_by = relationship("User", foreign_keys=[modified_by])
    mentions_business_id = relationship("Business", foreign_keys=[business_id])
    mentions_user_id = relationship("User", foreign_keys=[user_id])
    related_file_state_id = relationship("FileState", foreign_keys=[file_state_id])
    related_file_id = relationship("File", foreign_keys=[file_id])
    related_mention_rel_text_id = relationship("CtakesMentionsRelText", foreign_keys=[mention_rel_text_id])
    annotation_relation = relationship('CtakesMentions',
                                       secondary=annotation_relationship,
                                       primaryjoin=id == annotation_relationship.c.annotation_1_id,
                                       secondaryjoin=id == annotation_relationship.c.annotation_2_id)
