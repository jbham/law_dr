import sys
import traceback
import aiohttp
import json
from typing import Dict, List, Optional
from dateutil.parser import parse

from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session

from app.crud.aioSession import get_session
from app.crud.file import get_by_file_ids
from app.crud.case import get_by_case_id, confirm_case_id_with_biz_id_helper_func
from app.crud.search import get_all_confirmed_visit_dates, show_me_pdf_from_db, get_all_terms
from app.api.utils.db import get_db
from app.api.utils.security import get_current_active_user
from app.db_models.user import User as DBUser
from app.models.search import SolrSearchResults, VisitDates, PresetCatFiltersSearchResults, PDFCordBboxPageNo
from app.models.file import ShowMePDF
import urllib.parse
from app.db_models.file import FileState as DBFileState
from starlette.responses import Response
from app.api.api_logging import logger

router = APIRouter()

session = aiohttp.ClientSession()

all_categories = {"t116": "Amino Acid, Peptide, or Protein",
                  "t020": "Acquired Abnormality",
                  "t052": "Activity",
                  "t100": "Age Group",
                  "t087": "Amino Acid Sequence",
                  "t011": "Amphibian",
                  "t190": "Anatomical Abnormality",
                  "t008": "Animal",
                  "t017": "Anatomical Structure",
                  "t195": "Antibiotic",
                  "t194": "Archaeon",
                  "t123": "Biologically Active Substance",
                  "t007": "Bacterium",
                  "t031": "Body Substance",
                  "t022": "Body System",
                  "t053": "Behavior",
                  "t038": "Biologic Function",
                  "t012": "Bird",
                  "t029": "Body Location or Region",
                  "t091": "Biomedical Occupation or Discipline",
                  "t122": "Biomedical or Dental Material",
                  "t023": "Body Part, Organ, or Organ Component",
                  "t030": "Body Space or Junction",
                  "t026": "Cell Component",
                  "t043": "Cell Function",
                  "t025": "Cell",
                  "t019": "Congenital Abnormality",
                  "t103": "Chemical",
                  "t120": "Chemical Viewed Functionally",
                  "t104": "Chemical Viewed Structurally",
                  "t185": "Classification",
                  "t201": "Clinical Attribute",
                  "t200": "Clinical Drug",
                  "t077": "Conceptual Entity",
                  "t049": "Cell or Molecular Dysfunction",
                  "t088": "Carbohydrate Sequence",
                  "t060": "Diagnostic Procedure",
                  "t056": "Daily or Recreational Activity",
                  "t203": "Drug Delivery Device",
                  "t047": "Disease or Syndrome",
                  "t065": "Educational Activity",
                  "t069": "Environmental Effect of Humans",
                  "t196": "Element, Ion, or Isotope",
                  "t050": "Experimental Model of Disease",
                  "t018": "Embryonic Structure",
                  "t071": "Entity",
                  "t126": "Enzyme",
                  "t204": "Eukaryote",
                  "t051": "Event",
                  "t099": "Family Group",
                  "t021": "Fully Formed Anatomical Structure",
                  "t013": "Fish",
                  "t033": "Finding",
                  "t004": "Fungus",
                  "t168": "Food",
                  "t169": "Functional Concept",
                  "t045": "Genetic Function",
                  "t083": "Geographic Area",
                  "t028": "Gene or Genome",
                  "t064": "Governmental or Regulatory Activity",
                  "t102": "Group Attribute",
                  "t096": "Group",
                  "t068": "Human-caused Phenomenon or Process",
                  "t093": "Health Care Related Organization",
                  "t058": "Health Care Activity",
                  "t131": "Hazardous or Poisonous Substance",
                  "t125": "Hormone",
                  "t016": "Human",
                  "t078": "Idea or Concept",
                  "t129": "Immunologic Factor",
                  "t055": "Individual Behavior",
                  "t197": "Inorganic Chemical",
                  "t037": "Injury or Poisoning",
                  "t170": "Intellectual Product",
                  "t130": "Indicator, Reagent, or Diagnostic Aid",
                  "t171": "Language",
                  "t059": "Laboratory Procedure",
                  "t034": "Laboratory or Test Result",
                  "t015": "Mammal",
                  "t063": "Molecular Biology Research Technique",
                  "t066": "Machine Activity",
                  "t074": "Medical Device",
                  "t041": "Mental Process",
                  "t073": "Manufactured Object",
                  "t048": "Mental or Behavioral Dysfunction",
                  "t044": "Molecular Function",
                  "t085": "Molecular Sequence",
                  "t191": "Neoplastic Process",
                  "t114": "Nucleic Acid, Nucleoside, or Nucleotide",
                  "t070": "Natural Phenomenon or Process",
                  "t086": "Nucleotide Sequence",
                  "t057": "Occupational Activity",
                  "t090": "Occupation or Discipline",
                  "t109": "Organic Chemical",
                  "t032": "Organism Attribute",
                  "t040": "Organism Function",
                  "t001": "Organism",
                  "t092": "Organization",
                  "t042": "Organ or Tissue Function",
                  "t046": "Pathologic Function",
                  "t072": "Physical Object",
                  "t067": "Phenomenon or Process",
                  "t039": "Physiologic Function",
                  "t121": "Pharmacologic Substance",
                  "t002": "Plant",
                  "t101": "Patient or Disabled Group",
                  "t098": "Population Group",
                  "t097": "Professional or Occupational Group",
                  "t094": "Professional Society",
                  "t080": "Qualitative Concept",
                  "t081": "Quantitative Concept",
                  "t192": "Receptor",
                  "t014": "Reptile",
                  "t062": "Research Activity",
                  "t075": "Research Device",
                  "t089": "Regulation or Law",
                  "t167": "Substance",
                  "t095": "Self-help or Relief Organization",
                  "t054": "Social Behavior",
                  "t184": "Sign or Symptom",
                  "t082": "Spatial Concept",
                  "t024": "Tissue",
                  "t079": "Temporal Concept",
                  "t061": "Therapeutic or Preventive Procedure",
                  "t005": "Virus",
                  "t127": "Vitamin",
                  "t010": "Vertebrate"}

core = "mentions"
url = f"http://localhost:8983/solr/{core}/select"


@router.get("/search/all/", tags=["search"], response_model=List[VisitDates])
def return_all(*, db: Session = Depends(get_db), case_id: int,
               search_term: Optional[str] = None, file_id: Optional[int] = None, file_state_id: Optional[int] = None,
               current_user: DBUser = Depends(get_current_active_user)):
    # Variables:
    index = 0
    skip_first_VD_results = False

    # confirm_case_id_with_biz_id = get_by_case_id(db, id=case_id, user_details=current_user)
    confirm_case_id_with_biz_id_helper_func(db, case_id, current_user)

    # ---- All Visit Dates by individual files
    cvd = get_all_confirmed_visit_dates(db, case_id, search_term=search_term, user_details=current_user)
    results = []
    for i, c in enumerate(cvd):
        parsed_date = c["confirmed_visit_date"]
        if parsed_date:
            parsed_date = parsed_date.replace("o", "0").replace("O", "0")
            try:
                parsed_date = parse(parsed_date)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)

        visit_date_obj = VisitDates(string_to_date=parsed_date,
                                    parsed_date_to_string=f"{parsed_date.date()}",
                                    confirmed_visit_date=c["confirmed_visit_date"],
                                    file_id=c["file_id"],
                                    file_state_id=c["id"],
                                    last_modified_instant=c["last_modified_instant"],
                                    name=c["name"]
                                    )

        # this is what the search came in for....do the search here for the specific file id
        # for EVERYTHING search, it happens at the bottom
        if file_id == c["file_id"] and file_state_id == c["id"]:
            resp = get_all_terms(db, visit_date=visit_date_obj, case_id=case_id, search_term=search_term, user_details=current_user)
            visit_date_obj.all_terms = resp
            skip_first_VD_results = True

        results.append(visit_date_obj)

    # sorting so the visit date becomes a timeline
    results = sorted(results, key=lambda x: x.string_to_date)

    # ---- All Terms for the very first visit date
    if len(results) > 0 and not skip_first_VD_results:
        resp = get_all_terms(db, visit_date=results[index], case_id=case_id, search_term=search_term, user_details=current_user)
        results[index].all_terms = resp

    return results


# -------------everything below here will be deprecated soon because we may move off of Solar and just rely on Postgres' search text capabilities
@router.get("/search/visitdates/", tags=["search"], response_model=List[VisitDates])
def faceted_search(*, db: Session = Depends(get_db), case_id: int,
                   current_user: DBUser = Depends(get_current_active_user)):
    cvd = get_all_confirmed_visit_dates(db, case_id, user_details=current_user)

    results = []
    for i, c in enumerate(cvd):
        parsed_date = c.confirmed_visit_date
        if parsed_date:
            parsed_date = parsed_date.replace("o", "0").replace("O", "0")
            try:
                parsed_date = parse(parsed_date)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)

        results.append(VisitDates(string_to_date=parsed_date,
                                  parsed_date_to_string=f"{parsed_date.date()}",
                                  confirmed_visit_date=c.confirmed_visit_date,
                                  file_id=c.file_id,
                                  last_modified_instant=c.last_modified_instant,
                                  name=c.name
                                  ))

    results = sorted(results, key=lambda x: x.string_to_date)

    return results


@router.get("/search/category", tags=["search"], response_model=SolrSearchResults)
async def faceted_search(*, db: Session = Depends(get_db), start: int = 0, limit: int = 25, file_id: int, category: str,
                         current_user: DBUser = Depends(get_current_active_user)):
    confirm_case_id_with_biz_id = get_by_file_ids(db, ids=[file_id], user_details=current_user)

    if not confirm_case_id_with_biz_id:
        logger.info(f"Invalid file_id of value {file_id} found for business_id {current_user.business_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid details passed.",
        )

    cat = None

    if category:
        if category.__eq__("Body Part/Organ"):
            cat = "t023"
        else:
            for k, v in all_categories.items():
                if category.__eq__(v):
                    cat = k
                    break

    else:
        logger.info(f"No category found for variable {category} and business_id {current_user.business_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid details passed.",
        )

    params = {"fq": f"business_id%3A{current_user.business_id}%20AND%20file_id%3A{file_id}",
              "q": f"tui%3A{cat}", "rows": min(limit, 500), "start": start}

    local_session = await get_session()
    resp = await local_session.get(url, params=params)
    res = json.loads(await resp.text())
    result = res["response"]
    return result


@router.get("/search/vdtxt", tags=["search"], response_model=SolrSearchResults)
async def search_text_for_visit_date(*, db: Session = Depends(get_db), file_id: int, cvd: Optional[str],
                                     txt: Optional[str], start: int = 0,
                                     limit: int = 25, current_user: DBUser = Depends(get_current_active_user)):
    if not cvd and not txt:
        logger.info(f"Visit Date and Text passed was Blank for file_id of value {file_id} and"
                    f" business_id {current_user.business_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid details passed.",
        )

    main_str = f"business_id:{current_user.business_id} AND file_id:{file_id} "

    if cvd:
        cvd = cvd.split(",")
        str_h = " AND ("
        cvd_str = f"confirmed_visit_date:"
        for i, c in enumerate(cvd):
            if i > 0:
                str_h = str_h + " OR "
            str_h = str_h + cvd_str + c

        str_h += ")"
        main_str += str_h

    if txt:
        main_str += f" AND (text:{txt} OR full_text:{txt})"

    confirm_case_id_with_biz_id = get_by_file_ids(db, ids=[file_id], user_details=current_user)

    if not confirm_case_id_with_biz_id:
        logger.info(f"Invalid file_id of value {file_id} found for business_id {current_user.business_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid details passed.",
        )

    # in case someone ever tries to temper with frontend payload and try to get other business' details:
    if main_str.count("business_id") > 1:
        logger.warn(f"Looks like someone tried to temper with frontend payload and added business_id twice: "
                    f"\nmain_str: {main_str}")
        raise HTTPException(
            status_code=400,
            detail="Invalid details passed.",
        )

    params = {"fq": main_str,
              "q": "%2A%3A%2A",
              "rows": limit,
              "start": start}

    local_session = await get_session()
    resp = await local_session.get(url, params=params)
    res = json.loads(await resp.text())
    distinct_full_text = []
    result = res["response"]
    for i, r in enumerate(result["docs"]):
        if r["full_text"] + r["confirmed_visit_date"] not in distinct_full_text:
            distinct_full_text.append(r["full_text"] + r["confirmed_visit_date"])
        else:
            result["docs"].pop(i)

    # numfound etc etc
    return result


# new functions start here
@router.get("/search/facet", tags=["search"], response_model=List[Dict[str, int]])
async def faceted_search(*, db: Session = Depends(get_db), case_id: int,
                         current_user: DBUser = Depends(get_current_active_user),
                         response: Response):
    # confirm_case_id_with_biz_id = get_by_case_id(db, id=case_id, user_details=current_user)
    #
    # if not confirm_case_id_with_biz_id:
    #     logger.info(f"Invalid case_id of value {case_id} found for business_id {current_user.business_id}")
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Invalid details passed.",
    #     )

    confirm_case_id_with_biz_id_helper_func(db, case_id, current_user)

    params = {"q": "%2A:%2A",
              "fq": f"business_id:{current_user.business_id}%20AND%20case_id:{case_id}",
              # %20AND%20"
              # f"concept_attributes:%28t037%20OR%20t047%20OR%20t184%20OR%20t190%20OR%20t017%29",
              "facet": "true",
              # "facet.field": "tui",
              "facet.field": "category",
              "rows": "0",
              "facet.mincount": "1"}

    local_session = await get_session()
    resp = await local_session.get(url, params=params)
    res = json.loads(await resp.text())

    if "error" in res:
        logger.info(f"Exception occurred for business_id: {current_user.business_id} while fetching file_id: {case_id} "
                    f"with below exception. \n {res['error']['trace']}")
        raise HTTPException(
            status_code=res["error"]["code"],
            detail="Invalid details passed.",
        )

    result = res["facet_counts"]["facet_fields"]["category"]
    return_list = []
    for i in range(0, len(result), 2):
        # if we were faceting by TUI or CUI then we would need line
        # obj = {str(all_categories[result[i]]): result[i + 1]}

        # but we are faceting by Category for easy viewing for end user

        if str(result[i]) in ['Sign Or Symptom', 'Medication', 'Body Site', 'Medical Procedure', 'Disease Disorder']:
            obj = {str(result[i]): result[i + 1]}

            return_list.append(obj)

    # response.headers["cache-control"] = f"private, max-age={int(86400)}"
    return return_list


@router.get("/search/presetcatfilters", tags=["search"], response_model=PresetCatFiltersSearchResults)
async def preset_cat_filters(*,
                             db: Session = Depends(get_db),
                             case_id: int,
                             category: str,
                             # txt: Optional[str],
                             # start: int = 0,
                             # limit: int = 25,
                             current_user: DBUser = Depends(get_current_active_user),
                             response: Response):
    confirm_case_id_with_biz_id_helper_func(db, case_id, current_user)

    f_pivot = "category,text,confirmed_visit_date,id"

    params = {
        "q": "*:*",
        "fq": f"category:\"{category}\" AND business_id:{current_user.business_id} AND case_id:{case_id}",
        "facet.pivot": f_pivot,
        "facet": "true",
        "rows": "0",
        "facet.pivot.mincount": "1",
        "facet.limit": "-1"
    }

    local_session = await get_session()
    resp = await local_session.get(url, params=urllib.parse.urlencode(params))
    res = json.loads(await resp.text())

    if "error" in res:
        logger.info(f"Exception occurred for business_id: {current_user.business_id} while fetching file_id: {case_id} "
                    f"with below exception. \n {res['error']['trace']}")
        raise HTTPException(
            status_code=res["error"]["code"],
            detail="Invalid details passed.",
        )

    d: PresetCatFiltersSearchResults = PresetCatFiltersSearchResults(field=None, value=None, count=None, pivot=None)
    if len(res["facet_counts"]["facet_pivot"][f_pivot]) > 0:
        d = res["facet_counts"]["facet_pivot"][f_pivot][0]
        # response.headers["cache-control"] = f"private, max-age={int(86400)}"
    return d


@router.get("/search/listofpdfs", tags=["search"], response_model=List[Optional[ShowMePDF]])
def show_me_pdf_search(*, db: Session = Depends(get_db), case_id: int,
                       current_user: DBUser = Depends(get_current_active_user),
                       response: Response):
    # confirm_case_id_with_biz_id = get_by_case_id(db, id=case_id, user_details=current_user)
    #
    # if not confirm_case_id_with_biz_id:
    #     logger.info(f"Invalid case_id of value {case_id} found for business_id {current_user.business_id}")
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Invalid details passed.",
    #     )

    confirm_case_id_with_biz_id_helper_func(db, case_id, current_user)
    results = show_me_pdf_from_db(db, case_id, user_details=current_user)

    # response.headers["cache-control"] = f"private, max-age={int(86400)}"

    return results


@router.get("/search/childfiles", tags=["search"], response_model=PresetCatFiltersSearchResults)
async def show_me_pdf_from_solr(*,
                                db: Session = Depends(get_db),
                                case_id: int,
                                file_id: int,
                                current_user: DBUser = Depends(get_current_active_user),
                                response: Response):
    confirm_case_id_with_biz_id_helper_func(db, case_id, current_user)

    f_pivot = "file_id,s3_file_dest"

    params = {
        "q": "*:*",
        "fq": f"file_id:\"{file_id}\" AND business_id:{current_user.business_id} AND case_id:{case_id}",
        "facet.pivot": f_pivot,
        "facet": "true",
        "rows": "0",
        "facet.pivot.mincount": "1",
        "facet.limit": "-1"
    }

    local_session = await get_session()
    resp = await local_session.get(url, params=urllib.parse.urlencode(params))
    res = json.loads(await resp.text())

    if "error" in res:
        logger.info(f"Exception occurred for business_id: {current_user.business_id} while fetching file_id: {case_id} "
                    f"with below exception. \n {json.dumps(res['error'], indent=4)}")
        raise HTTPException(
            status_code=res["error"]["code"],
            detail="Invalid details passed.",
        )

    d: PresetCatFiltersSearchResults = PresetCatFiltersSearchResults(field=None, value=None, count=None, pivot=None)
    if len(res["facet_counts"]["facet_pivot"][f_pivot]) > 0:
        d = res["facet_counts"]["facet_pivot"][f_pivot][0]
        # response.headers["cache-control"] = f"private, max-age={int(86400)}"
    return d


@router.get("/search/pdfcords", tags=["search"], response_model=PDFCordBboxPageNo)
async def get_pdf_cords(*,
                        db: Session = Depends(get_db),
                        case_id: int,
                        m_id: int,
                        current_user: DBUser = Depends(get_current_active_user),
                        response: Response):
    confirm_case_id_with_biz_id_helper_func(db, case_id, current_user)

    params = {
        "q": "*:*",
        "fq": f"id:{m_id} AND business_id:{current_user.business_id} AND case_id:{case_id}",
        "fl": "full_text_bbox, page_number"
    }

    local_session = await get_session()
    resp = await local_session.get(url, params=urllib.parse.urlencode(params))
    res = json.loads(await resp.text())

    if "error" in res:
        logger.info(f"Exception occurred for business_id: {current_user.business_id} while fetching file_id: {case_id} "
                    f"with below exception. \n {res['error']['trace']}")
        raise HTTPException(
            status_code=res["error"]["code"],
            detail="Invalid details passed.",
        )
    obj_to_return = {}
    if len(res["response"]["docs"]) > 0:
        obj_to_return = res["response"]["docs"][0]
    else:
        obj_to_return["full_text_bbox"] = ""
        obj_to_return["page_number"] = 0

    # Cache-Control:public, max-age=31536000
    # response.headers["cache-control"] = f"private, max-age={int(86400)}"
    return obj_to_return
