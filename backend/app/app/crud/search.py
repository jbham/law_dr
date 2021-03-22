from typing import List, Optional, Dict
from dateutil.parser import parse
import traceback
import sys

from sqlalchemy import and_, func, case, literal_column

from app.db_models.file import FileState as DBFileState
from app.db_models.file import File as DBFile
from app.db_models.ctakes_mentions import CtakesMentions, CtakesMentionsRelText, annotation_relationship
from app.db_models.business import Business
from app.models.search import VisitDates

s3_file_global_url = []


def get_all_terms(db_session, visit_date: VisitDates, case_id: int,
                  search_term: Optional[str] = None, *, user_details=None) -> Optional[List[object]]:
    searchString = "and cm.text = :searchTerm"
    result = db_session.execute(f"""
                    select
                        cm.id, cm.file_id, cm.file_state_id ,  cm."begin" , cm."end" , 
                        case when cm.annotation_type = 'EventMention' then 'Event'
                        else 
                            case when cm.annotation_type = 'MeasurementAnnotation' then 'Measurement'
                            else 
                                case when cm.annotation_type = 'DrugChangeStatusAnnotation' then 'Drug Change Status'
                                else 
                                    case when cm.annotation_type = 'StrengthUnitAnnotation' then 'Drug Strength Unit'
                                    else
                                        case when cm.annotation_type = 'FrequencyUnitAnnotation' then 'Drug Frequency'
                                        else
                                            case when cm.annotation_type = 'LabMention' then 'Lab Details'
                                            else
                                                case when cm.annotation_type = 'MedicationMention' then 'Medication'
                                                else
                                                    case when cm.annotation_type = 'ProcedureMention' then 'Procedure'
                                                    else
                                                        case when cm.annotation_type = 'LabValueModifier' then 'Lab Value'
                                                        else
                                                            case when cm.annotation_type = 'AnatomicalSiteMention' then 'Anatomical Site'
                                                            else
                                                                case when cm.annotation_type = 'RouteAnnotation' then 'Medication Route'
                                                                else
                                                                    case when cm.annotation_type = 'StrengthAnnotation' then 'Medication Strength'
                                                                    else
                                                                        case when cm.annotation_type = 'SignSymptomMention' then 'Sign or Symptoms'
                                                                        else
                                                                            case when cm.annotation_type = 'DiseaseDisorderMention' then 'Disease or Disorder'
                    --											    		else
                                                                            end
                                                                        end
                                                                    end
                                                                end
                                                            end
                                                        end
                                                    end
                                                end
                                            end
                                        end
                                    end
                                end 
                            end
                        end as annotation_type ,
                    --    cm.annotation_type ,
                        cm."text" , cm.polarity , cm.page_number , -- cm.visit_date ,
                        cm.bucket , cm.s3_file_dest , cm.body_region , cm.body_side , -- cm.relations, 
                        mrt.full_text , mrt.full_text_bbox,
                        rel.related_ids as related_ids ,
                        fs2.confirmed_visit_date 
                    from
                        public.sf_ctakes_mentions cm
                    join public.mentions_rel_text mrt on
                        mrt.business_id = cm.business_id
                        and mrt.id = cm.mention_rel_text_id
                    join public.file f2 on 
                        f2.business_id = cm.business_id 
                        and f2.id = cm.file_id 
                    join public.file_state fs2 on 
                        fs2.business_id = cm.business_id
                        and fs2.file_id  = f2.id 
                        and fs2.id = cm.file_state_id
                    join public."case" c2 on 
                        c2.id = f2.case_id 
                        and c2.business_id = f2.business_id 
                    left join (
                        select
                            annotation_1_id,
                            array_agg(annotation_2_id) as related_ids,
                            business_id 
                        from
                            annotation_relationships ar
                        where business_id = :case_business_id
                        group by
                            annotation_1_id, business_id 
                    ) rel on 
                        rel.business_id = cm.business_id 
                        and rel.annotation_1_id = cm.id 
                    where
                        annotation_type not in 
                        ('Modifier', 'SubjectModifier', 'Predicates')
                    --    ('AnatomicalSiteMention', 'DrugChangeStatusAnnotation', 'DiseaseDisorderMention', 
                    --    'MedicationMention', 'ProcedureMention', 'SignSymptomMention', 'LabMention', 'EventMention')
                        and c2.id = :passed_case_id
                        and c2.business_id = :case_business_id
                        and cm.file_id = :file_id
	                    and cm.file_state_id = :file_state_id
                        {searchString if search_term else ""}
    """, {"passed_case_id": case_id,
          "case_business_id": user_details.business_id,
          "file_id": visit_date.file_id,
          "file_state_id": visit_date.file_state_id,
          "searchTerm": search_term})
    # Record = namedtuple('Record123', result.keys())
    # records = [Record(*r)._asdict() for r in result.fetchall()]
    records = [dict(r) for r in result.fetchall()]

    # finalized_results = []
    # date_holder = []
    # for r in result.fetchall():
    #     row = dict(r)
    #
    #     parsed_date = row["confirmed_visit_date"]
    #     if parsed_date:
    #         parsed_date = parsed_date.replace("o", "0").replace("O", "0")
    #         try:
    #             parsed_date = parse(parsed_date)
    #             row["parsed_date_to_string"] = f"{parsed_date.date()}"
    #             row["string_to_date"] = parsed_date
    #             date_holder.append(parsed_date)
    #             # TODO: REMOVE AFTER DEBUG
    #
    #         except Exception as e:
    #             traceback.print_exc(file=sys.stdout)
    #
    #     finalized_results.append(row)

    return records


def get_all_confirmed_visit_dates(db_session, case_id: int, search_term: Optional[str] = None, *,
                                  user_details=None) -> Optional[List[object]]:  # List[Optional[DBFileState]]:
    # return db_session.query(DBFileState.id,
    #                         DBFileState.file_id,
    #                         DBFileState.last_modified_instant,
    #                         DBFileState.confirmed_visit_date,
    #                         DBFile.name,
    #                         literal_column("'string_to_date'")) \
    #     .join(DBFile, and_(DBFile.id == DBFileState.file_id,
    #                        DBFile.business_id == user_details.business_id,
    #                        DBFileState.business_id == user_details.business_id, )) \
    #     .filter(DBFile.case_id == case_id) \
    #     .filter(DBFileState.business_id == user_details.business_id) \
    #     .filter(DBFileState.confirmed_visit_date != None) \
    #     .all()

    searchString = "and scm.text = :searchTerm"
    result = db_session.execute(f"""
            select
                distinct fs2.id,
                fs2.file_id ,
                fs2.last_modified_instant ,
                f."name" ,
                null as "string_to_date",
                fs2.confirmed_visit_date 
            from
                public.file f
            join public.file_state fs2 on
                fs2.file_id = f.id
                and fs2.business_id = f.business_id
            join public."case" c on
                c.business_id = f.business_id
                and c.id = f.case_id 
            join sf_ctakes_mentions scm on 
                scm.file_id = fs2.file_id 
                and scm.file_state_id = fs2.id 
                and scm.business_id  = fs2.business_id 	
            where
                c.id = :case_id
                and c.business_id = :business_id
                and fs2.confirmed_visit_date is not null
                {searchString if search_term else ""}
            """, {
        "case_id": case_id,
        "business_id": user_details.business_id,
        "searchTerm": search_term
    })

    records = [dict(r) for r in result.fetchall()]
    return records


# Used sometime in the past
def get_text_by_visit_date(db_session, file_id: int, *,
                           user_details=None) -> List[Optional[DBFileState]]:
    return db_session.query(DBFileState) \
        .filter(DBFileState.file_id == file_id) \
        .filter(DBFileState.business_id == user_details.business_id) \
        .filter(DBFileState.confirmed_visit_date != None) \
        .all()


# Used sometime in the past
def show_me_pdf_from_db(db_session, case_id: int, *,
                        user_details=None) -> List[Optional[DBFile]]:
    return db_session.query(DBFile) \
        .join(Business, and_(Business.id == DBFile.business_id,
                             DBFile.business_id == user_details.business_id)) \
        .filter(DBFile.case_id == case_id) \
        .all()

# async def loop_over_pivots(data):
#     global s3_file_global_url
#     for d in data:
#         if "pivot" in d:
#             f = await loop_over_pivots(d["pivot"])
#             obj = {
#                 "key": d["field"],
#                 "label": d["value"],
#                 "nodes": [f]}
#             return obj
#         else:
#             return {
#                 "key": d['value'],
#                 "label": str(d['value']).split("/")[-1],
#                 "nodes": [],
#             }
