from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from typing import List, Dict




class SearchDocs(BaseModel):
    id: str = None
    business_id: int = None
    text: str = None
    full_text: str = None
    file_state_id: int = None
    file_id: int = None
    polarity: int = None
    page_number: int = None
    confirmed_visit_date: str = None
    modified_date: datetime = None


class SolrSearchResults(BaseModel):
    numFound: int
    start: Optional[int]
    docs: Optional[List[SearchDocs]]


class VisitDates(BaseModel):
    confirmed_visit_date: str = None
    file_id: int = None
    file_state_id: int = None
    last_modified_instant: datetime = None
    name: str = None
    string_to_date: datetime = None
    parsed_date_to_string: str = None
    all_terms: List = None

    class Config:
        orm_mode = True


class PresetCatFiltersSearchResults(BaseModel):
    field: str = None
    value: str = None
    count: int = None
    pivot: Optional[List] = None


class PDFCordBboxPageNo(BaseModel):
    full_text_bbox: str = None
    page_number: int = None
