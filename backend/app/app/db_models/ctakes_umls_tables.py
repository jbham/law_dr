from sqlalchemy import (Column, Integer, String, BigInteger)

from app.db.base_class import Base


class CUI_TERMS(Base):
    __tablename__ = "CUI_TERMS"

    CUI = Column(BigInteger)
    RINDEX =  Column(Integer)
    TCOUNT = Column(Integer)
    TEXT = Column(String)
    RWORD = Column(String, primary_key=True, index=True)


class TUI(Base):
    __tablename__ = "TUI"

    CUI = Column(BigInteger)
    TUI = Column(Integer, primary_key=True)


class PREFTERM(Base):
    __tablename__ = "PREFTERM"

    CUI = Column(BigInteger)
    PREFTERM = Column(String, primary_key=True)


class RXNORM(Base):
    __tablename__ = "RXNORM"

    CUI = Column(BigInteger)
    RXNORM = Column(BigInteger, primary_key=True)

    """CREATE TABLE RXNORM(CUI BIGINT,RXNORM BIGINT);
CREATE INDEX IDX_RXNORM ON RXNORM(CUI);"""


class ICD10(Base):
    __tablename__ = "ICD10"

    CUI = Column(BigInteger)
    ICD10 = Column(String, primary_key=True)


class ICD10PCS(Base):
    __tablename__ = "ICD10PCS"

    CUI = Column(BigInteger)
    ICD10PCS = Column(String, primary_key=True)

