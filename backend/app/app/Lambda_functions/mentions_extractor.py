import sys
import traceback
import datetime
import json
import fitz
import re
import boto3
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.extras import Json as PGJson, DictCursor

dummy_string = "SamKamJas"
dummy_page_number = 100000


# TODO - refactor this
# temporary solution
class PDFTestRelatedAction:

    def __init__(self, text, hopi_regex, cc_regex, reason_for_regex):
        self.text = str(text)
        self.hopi_regex = hopi_regex
        self.cc_regex = cc_regex
        self.reason_for_regex = reason_for_regex

    # not used
    def chief_complaint(self):
        re1 = '(Chief)'  # Variable Name 1
        re2 = '.*?'  # Non-greedy match on filler
        re3 = '(Complaint)'  # Variable Name 2

        url = re.findall(
            '[a-zA-Z][a-zA-Z][a-zA-Z][a-zA-Z]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            self.text)

        for u in url:
            text = self.text.replace(u, "")

        rg = re.compile(re1 + re2 + re3, re.IGNORECASE | re.DOTALL)
        m = rg.search(self.text)
        return m

    def clean_text(self):
        self.text = self.text.replace(" \n", " ") \
            .replace("  ", " ") \
            .replace("\n ", " ") \
            .replace("(\n", "(") \
            .replace("\n.", ".")

    def section_finder_regex(self):
        # find either:
        # CC/HPI
        # HISTORY OF PRESENT ILLNESS
        # HISTORY OF THE PRESENT ILLNESS
        # HISTORY OF PRESENT CONDITION
        # HISTORY OF THE PRESENT CONDITION
        # HISTORY OF PHYSICAL ILLNESS
        # HISTORY OF THE PHYSICAL ILLNESS
        # HISTORY OF PHYSICAL CONDITION (HPI, Problem by Problem)
        # HISTORY OF THE PHYSICAL CONDITION (HPI, Problem by Problem)
        history_of_present_illness = "(?:(?:CC\/HPI:)|(?:(?:HISTORY OF (?:THE )?(?:PRESENT |PHYSICAL )?(?:CONDITION|ILLNESS))(?: \(HPI(?:, PROBLEM BY PROBLEM)?\))*:?))"

        # find either:
        # CHIEF COMPLAINTS
        # PRIMARY COMPLAINTS
        # CHIEF <anything in between> COMPLAINTS
        # PRIMARY <anything in between> COMPLAINTS

        chief_complaint = "(?:CHIEF|PRIMARY).*COMPLAINTS?[\t ]*:"

        # find
        # Reason for Appointment
        # Reason for Exam
        reason_for = "REASON.*FOR.*?(?:APPOINTMENT|EXAM)"

        hopi = self.hopi_regex.search(self.text.upper())
        cc_found = self.cc_regex.search(self.text.upper())
        reason_for = self.reason_for_regex.search(self.text.upper())

        # hopi = re.findall(history_of_present_illness, self.text.upper())
        # cc_found = re.findall(chief_complaint, self.text.upper())
        # reason_for = re.findall(reason_for, self.text.upper())

        return hopi, cc_found, reason_for


def perform_regex(s):
    list_1 = list()

    # replace newline, tab or space between numbers
    # this may replace legitimate newlines as well
    # p = re.compile(r"[\d]\s[\d]")
    # list_1.append(p.finditer(s))

    # replace newline between numbers
    # p = re.compile(r"[\d]\n[\d]")
    # list_1.append(p.finditer(s))

    # replace newline character between a single UPPER/lower case character on left hand side
    # and one or more multiple lower case characters on right hand side which starts at the end of a line
    # example:
    """
    Actual: tops j
            aspal

    Expected:
            tops jaspal

    OR 

    Actual:     tops J
                aspal

    Actual:     tops Jaspal
    """
    # p = re.compile(r" \b[a-z]{1}\n[a-z]+")
    # list_1.append(p.finditer((s)))

    # find newline characters between a single UPPER case letter on left hand side
    # and one of more multiple lower case characters on right hand side
    # example:
    """
    Actual:
            T
            oday and 
            t
            hought

    Expected:    
            Today and 
            thought
    """

    # p = re.compile(r"\b[a-zA-Z]{1}\n[a-z]+")
    # list_1.append(p.finditer((s)))
    #
    # # look through all of the iters found above and do a replace
    # for lj in list_1:
    #     for g in lj:
    #         # print(g[0], g[0].replace("\n", ""))
    #
    #         # we don't want to replace valid characters with space in between them like:
    #         # I was .... a man was .... etc
    #         if not str(g[0]).lower().startswith(" a") \
    #                 or not str(g[0]).lower().startswith("a") \
    #                 or not str(g[0]).lower().startswith(" i") \
    #                 or not str(g[0]).lower().startswith("i"):
    #             s = s.replace(g[0], g[0].replace("\n", ""))

    # find the following:
    """
    Actual: C ervical Spine/Neck
    Expected: Cervical Spine/Neck    
    """

    # p = re.compile(r"\b[a-zA-Z]{1} [a-z]+")
    # f = p.finditer(s)
    # for g in f:
    #     s = s.replace(g[0], g[0].replace(" ", ""))

    # remove urls
    url = re.findall(
        '[a-zA-Z][a-zA-Z][a-zA-Z][a-zA-Z]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        s)

    for u in url:
        s = s.replace(u, "")

    # remove special dots
    s = re.sub(u"[|•]", "", s)

    # remove phone numbers
    p = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
    f = p.finditer(s)
    for g in f:
        s = s.replace(g[0], "")

    return s


def get_tui_cui(local_payload):
    tui = []
    cui = []
    for local_d in local_payload:
        # new_payload = {}
        # new_payload["cui"] = local_d["cui"]
        # new_payload["tui"] = local_d["tui"]
        if "tui" in local_d:
            tui.append(local_d["tui"])

        if "cui" in local_d:
            cui.append(local_d["cui"])

    # using set and then list to ensure we are putting ONLY the unique values
    return PGJson(list(set(tui))), PGJson(list(set(cui)))


def lambda_handler(event, context):
    start_time = datetime.datetime.utcnow()
    text = str()
    cc_related_term_found = False
    chief_complaint_tracker = dict()
    found_visit_date = False
    txt = 'Chief Complaints'
    re1 = '(Chief)'  # Variable Name 1
    re2 = '.*?'  # Non-greedy match on filler
    re3 = '(Complaint)'  # Variable Name 2
    cp_end = int()
    exception_occurred = bool()
    exception_for_db = None

    print(event)

    def find_overlapping_entries(full_list):
        local_idx_to_pop = []

        for idxl, ltr in enumerate(full_list):
            for li, lw in enumerate(full_list):
                if idxl != li and ltr["begin"] <= lw["begin"] and ltr["end"] >= lw["end"]:
                    local_idx_to_pop.append(li)

        return local_idx_to_pop

    def between_function(v_search, page_detail_list_func):
        # TODO: start needs in the same page and end needs to be on the same page as well
        # it possibles that half of the word is in one page and other half is on the next page

        for index_local, page_local in enumerate(page_detail_list_func):
            if page_local["starts_at"] <= v_search <= page_local["running_length"]:
                return index_local

    def omit_if_before_cp(end):
        return False if int(end) < cp_end else True

    def is_year_in_date(local_date_f):
        # visit date should have a year
        # in testing, we have identified that ctakes extracts measurements as dates
        # for instance, 4-6 is extracted as a valid date 4-6-2019
        # where year is the current year
        # so let's check if year is present in the string ctakes found

        start_year_for_visit_date = 1900
        local_append_visit_date = False

        while True:
            if str(start_year_for_visit_date) in local_date_f:
                local_append_visit_date = True
                break
            start_year_for_visit_date += 1

            # we don't want to check eternity either, break after year 2100
            # hopefully, our app is used at least until 2100 :)
            if start_year_for_visit_date > 2100:
                break

        return local_append_visit_date

    def is_dob_date(local_neighboring_words):
        local_leave_nvdl_loop = False
        # ignore DOBs
        not_visit_dates_list = ["DOB", "DATE OF BIRTH"]

        # we don't want to put DOB or DATE OF BIRTH dates into our agg_all_list LIST
        for nvdl in not_visit_dates_list:
            if nvdl in local_neighboring_words.upper():
                # remove them from the text we are processing
                # local_word_r.replace(nvdl, "").replace(date_f, "")

                # if visit date is not found...go back to top of the loop
                local_leave_nvdl_loop = True
                break

        return local_leave_nvdl_loop

    def is_visit_date_label(local_neighboring_words, local_master_list):

        local_found_visit_date = False

        # These terms are valid Visit dates
        # a list in progress and will be updates as we learn more about these dates
        visd_list = ["DATE OF SERVICE", "SERVICE DATE",
                     "ENCOUNTER DATE", "M0030", "FROM DATE",
                     "EXAM DATE",
                     # different variations of SOC dates...in case OCR doesnt recognize them
                     # correctly
                     "SOC", "SQC"]

        for visd in visd_list:
            if visd in local_neighboring_words.upper():
                # we found our visit date so no need to look further
                local_found_visit_date = True

                # once we have found our visit date then we should loop through
                # dateAnnotations and unmark/remove any other visit date that we may have found
                for inner_idx, inner_agg_list in enumerate(local_master_list):
                    # if inner_agg_list["category"] == "DateAnnotation":
                    # new_agg_all_list.append(inner_agg_list)
                    if "visit_date" in inner_agg_list:
                        del inner_agg_list["visit_date"]

        return local_found_visit_date, local_master_list

    if str(event["ctakes_exception"]) == 'completed':
        s3 = boto3.client('s3')

        history_of_present_illness = "(?:(?:CC\/HPI:)|(?:(?:HISTORY OF (?:THE )?(?:PRESENT |PHYSICAL )?(?:CONDITION|ILLNESS))(?: \(HPI(?:, PROBLEM BY PROBLEM)?\))*:?))"
        chief_complaint = "(?:CHIEF|PRIMARY).*COMPLAINTS?[\t ]*:"
        reason_for = "REASON.*FOR.*?(?:APPOINTMENT|EXAM)"

        hopi_regex = re.compile(history_of_present_illness, re.IGNORECASE | re.DOTALL)
        chief_complaints_regex = re.compile(chief_complaint, re.IGNORECASE | re.DOTALL)
        reason_for_regex = re.compile(reason_for, re.IGNORECASE | re.DOTALL)

        try:
            s3_object = s3.get_object(Bucket=event["bucket"], Key=event["file_name"])
            doc = fitz.open(None, s3_object["Body"].read(), "pdf")
            doc_len = len(doc)

            s3_object = s3.get_object(Bucket=event["bucket"], Key=event["json_file"])

            s = s3_object["Body"].read()
            ctakes_response = json.loads(s)

            unique_begin_end = list()

            master_list_pre = list()

            cat = [
                {'AnatomicalSiteMention': 'Body Site'},
                {'SignSymptomMention': 'Sign Or Symptom'},
                {'MedicationMention': 'Medication'},
                {'DiseaseDisorderMention': 'Disease Disorder'},
                {'ProcedureMention': 'Medical Procedure'},
                {'Predicates': 'Relations'},
                {'FractionAnnotation': 'Medication Fraction'},
                {'StrengthAnnotation': 'Drug Strength'},
                {'DrugChangeStatusAnnotation': 'Drug Change Identified'},
                {'FrequencyUnitAnnotation': 'Drug Frequency Unit'},
                {'RouteAnnotation': 'Drug prescribed route'},
                {'StrengthUnitAnnotation': 'Drug Strength'},
                {'LabMention': 'Lab'},
                {'MeasurementAnnotation': 'Measurement'},
                {'EventMention': 'General Event'},
                {'MedicationEventMention': 'Medication Event'},
                {'DateAnnotation': "Dates Only"},
                {'TimeMention': 'Date Time'},
                {'PersonTitleAnnotation': 'Person Title'},
                {'Modifier': 'Modifier'}
            ]

            # for k, v in ctakes_response.items():
            for c in cat:
                for k, v in c.items():
                    if k in ctakes_response:
                        for k1 in ctakes_response[k]:

                            # adding three conditions below:
                            # 1. We are ONLY processing unique entries. Many times, Procedures will have "leg"
                            #       and Events will have "leg" with the same "begin" and "end". So, we don't want that!
                            # 2. We add "SamKamJam" dummy string to sentences which end with numbers instead of period
                            #       or something else. CTAKES may find this dummy string as an "Event". So, we don't want
                            #       that either#
                            # 3. In "events', for some reason, it finds an apostrophes, double quotes as "events'. So,
                            #       we don't want that either!
                            # if int(k1["begin"] + k1["end"]) not in unique_begin_end \
                            if dummy_string not in k1["text"] \
                                    and int(k1["end"] - k1["begin"]) > 1:
                                local_str = str(k1["text"])

                                # don't add phone number looking terms
                                m = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", local_str)

                                # dont add SSN looking terms
                                n = re.search(r"\(?\d{3}\)?[-.\s]?\d{2}[-.\s]?\d{4}", local_str)

                                # don't add text where it is just a newline character like "\n"

                                if m is None and n is None and local_str != '\n':
                                    # CTAKES sometimes find one word predicate relations:
                                    # {"frameSet": "be.03","end": 794, "text": "was", "relations": [], "begin": 791}
                                    # we dont need those...so skip them
                                    if str(k) == "Predicates":
                                        if len(k1["relations"]) > 0:
                                            k1["category"] = str(v)
                                            master_list_pre.append(k1)
                                            unique_begin_end.append(int(k1["begin"] + k1["end"]))
                                    else:
                                        k1["category"] = str(v)
                                        master_list_pre.append(k1)
                                        unique_begin_end.append(int(k1["begin"] + k1["end"]))

            sorted_master = sorted(master_list_pre, key=lambda k: k['begin'])

            # find overlapping entry index
            # obj_to_pop = find_overlapping_entries(sorted_master)

            # filter out overlapping entries
            master_list = [mlp for idx_mlp, mlp in enumerate(sorted_master)] # if idx_mlp not in obj_to_pop]
            text_running_length = len(text)
            for i in range(0, doc_len):
                pno: int = i
                page = doc[pno]
                got_text = page.getText("dict")

                previous_original_text = ""

                for block_idx, nt in enumerate(got_text["blocks"]):
                    original_t = ""
                    if nt["type"] == 0:
                        for each_line in nt["lines"]:
                            for each_span in each_line["spans"]:
                                original_t += each_span["text"]

                        # let's keep the original text we obtained separate
                        ori_original_t = original_t

                        # if original_t ends with any number then add very unique dummy token
                        # so that CTAKES doesn't mess up in identifying measurements or date annotations
                        m = re.search(r'\d+$', original_t)
                        if m is not None:
                            original_t += f" {dummy_string}.\n"
                            # elif original_t.endswith("."):
                            #     original_t += "\n"
                        else:
                            original_t += "\n"

                        original_t_len = len(original_t)

                        # print(text_running_length, original_t_len, original_t)

                        # if "tendinosis" in original_t:
                        #     print("test")

                        # remove bullet list character
                        if u'\u2022' in original_t:
                            original_t = original_t.replace(u'\u2022', ".")

                        already_found_text = False

                        # loop through master_list and only check which ctakes annotation falls in this bbox
                        for idx_tbx, tbx in enumerate(master_list):

                            # if 'evening' in tbx["text"] and 'evening' in original_t:
                            #     print(tbx, original_t)
                            #     print("test")

                            if 'transmitted' in original_t and 'transmitted' in tbx["text"]:
                                print("test")

                            if tbx["begin"] == 8033 or tbx["end"] == 8044:
                                print("test")

                            if idx_tbx == 1020:
                                print("test")

                            if tbx["begin"] >= text_running_length \
                                    and tbx["end"] <= text_running_length + original_t_len:
                                bbox = list(nt["bbox"])
                                bbox.append(page.rect.width)
                                bbox.append(page.rect.height)

                                master_list[idx_tbx]["full_text"] = ori_original_t
                                master_list[idx_tbx]["full_text_bbox"] = str(bbox)
                                master_list[idx_tbx]["page_number"] = pno + 1

                                already_found_text = True

                            # ctakes may find important terms which fall into previous and current bbox
                            # lets handle that scenario here:
                            # split tbx["text"] based on newline char
                            if not already_found_text:
                                txt_to_prcs = str(tbx["text"])
                                if '\n' in txt_to_prcs:
                                    split = str(tbx["text"]).split("\n")

                                    if split[0] in previous_original_text and split[1] in original_t:
                                        bbox = list(nt["bbox"])
                                        bbox.append(page.rect.width)
                                        bbox.append(page.rect.height)

                                        master_list[idx_tbx]["full_text"] = ori_original_t
                                        master_list[idx_tbx]["full_text_bbox"] = str(bbox)
                                        master_list[idx_tbx]["page_number"] = pno + 1

                            if tbx["end"] > text_running_length + original_t_len:
                                break

                        text = text + original_t
                        text_running_length = len(text)
                        previous_original_text = original_t

                if not cc_related_term_found:
                    pdf_text_action = PDFTestRelatedAction(text,
                                                           hopi_regex,
                                                           chief_complaints_regex,
                                                           reason_for_regex)

                    hopi, cc, reason_for = pdf_text_action.section_finder_regex()

                    if hopi:
                        chief_complaint_tracker["start"] = hopi.span()[0]
                        chief_complaint_tracker["end"] = cp_end = hopi.span()[1]
                        cc_related_term_found = True

                    if cc:
                        chief_complaint_tracker["start"] = cc.span()[0]
                        chief_complaint_tracker["end"] = cp_end = cc.span()[1]
                        cc_related_term_found = True

                    if reason_for:
                        chief_complaint_tracker["start"] = reason_for.span()[0]
                        chief_complaint_tracker["end"] = cp_end = reason_for.span()[1]
                        cc_related_term_found = True

                # rg = re.compile(re1 + re2 + re3, re.IGNORECASE | re.DOTALL)
                # m = rg.search(text)
                # if m and not cc_found:
                #     chief_complaint["start"] = m.span()[0]
                #     chief_complaint["end"] = cp_end = m.span()[1]
                #     var1 = m.group(1)
                #     var2 = m.group(2)
                #     cc_found = True

            word_r = text

            for li, l in enumerate(master_list):
                # only check for DATES which SHOW UP before Chief Complaint
                if not found_visit_date:
                    # # print(li, l["text"])
                    date_f = str(l["text"])
                    try:
                        # if we have a valid date then we can work on further validations
                        if is_year_in_date(date_f):

                            # get 20 characters from left and 40 characters
                            # from the starting point of the string
                            # neighboring_words = \
                            #     word_r[int(word_r.index(date_f)) - 20:int(word_r.index(date_f)) + 40]
                            neighboring_words = word_r[int(l["begin"]) - 20:int(l["begin"]) + 40]

                            leave_nvdl_loop = is_dob_date(neighboring_words)

                            if leave_nvdl_loop:
                                continue

                            found_visit_date, master_list = is_visit_date_label(neighboring_words, master_list)

                            # we have reached until CHIEF complaint but did not find visit date
                            # so mark every date, which is before Chief Complaint, as visit date
                            if l["begin"] <= chief_complaint_tracker["start"] and not found_visit_date:
                                master_list[li]["visit_date"] = date_f

                            # sometimes SOC dates would show up after Chief Complaint
                            # ensure that we mark a date as VISIT date ONLY if they are listed in the list of possible
                            # VISIT DATE lables
                            elif l["begin"] >= chief_complaint_tracker["start"] and found_visit_date:
                                master_list[li]["visit_date"] = date_f

                            # we are either above or below CHIEF COMPLAINT and we found the exact VISIT date we are
                            # looking for. "is_visit_date_label" function negates every other date, which may have been
                            # marked as VISIT date
                            elif found_visit_date:
                                master_list[li]["visit_date"] = date_f

                    except Exception as x:
                        print(x)

            # find possible visit dates, page number for each entry in ctakes response
            # new_list = sorted(agg_all_list, key=lambda k: k['begin'])
            #
            # search_found = 0
            #
            # def new_list_recursive_loop(txt_local):
            #     idx_list = [ri for ri, g in enumerate(new_list) if str(g["text"]).upper() == txt_local]
            #     return idx_list
            #
            # curr_page = 0
            #
            # for index, nl in enumerate(new_list):
            #     if curr_page != nl["page_num"]:
            #         curr_page = nl["page_num"]
            #     else:
            #         if "match_found" not in nl:
            #             index_list = new_list_recursive_loop(str(nl["text"]).upper())
            #             for di, dx in enumerate(index_list):
            #                 new_list[dx]["match_found"] = di

            # for i in range(0, doc_len):
            #     page_detail = {}
            #     pno = i
            #
            #     page = doc[pno]
            #
            #     # get 20% of the word count and we can put that as a hit_max limit.
            #     # If the same search appears in more than 20% of the page
            #     # then the person should just read the whole document
            #     pages_20_percent_word_length = round(len(doc.getPageText(
            #         pno)) / 5)
            #
            #     page._cleanContents()
            #
            #     dl = page.getDisplayList()
            #     tp = dl.getTextPage()
            #
            #     for nl1, nl2 in enumerate(master_list):
            #         # look inside a page in which the parent for loop is in
            #
            #         if nl2["text"] == '30 minutes':
            #             print("test")
            #         if nl2["page_number"] == i + 1:
            #             tdxt = nl2["text"]
            #             rlist = tp.search(tdxt, hit_max=pages_20_percent_word_length)
            #             len_tdxt = str(tdxt).split(" ")
            #             master_list[nl1]["rect_coordinates"] = []
            #             for tg in rlist:
            #                 master_list[nl1]["rect_coordinates"].append(
            #                     dict(height=tg.height, width=tg.width, rects=tg.__dict__,
            #                          text_has_space=True if len(len_tdxt) > 1 else False))

            doc.close()

        except Exception as e:
            print(e)
            exception_occurred = True
            exception_for_db = traceback.print_exc(file=sys.stdout)

        try:

            db_outer_list = []
            rmt_list_1_text = []
            rmt_list_1 = []

            # unique visit dates
            uni_vd = []

            conn = psycopg2.connect(
                "dbname='starfizz' user='starfizz' host='starfizz.cqjzxqvvjp0y.us-west-2.rds.amazonaws.com' password='starfizz'")

            cur = conn.cursor(cursor_factory=DictCursor)

            # load related mention text and get their ids
            # and
            # also check how many visit dates we found in the same loop

            for idx, j in enumerate(master_list):
                # print(idx, j)
                if str(j["full_text"]) not in rmt_list_1_text:
                    # print(rmt_list_1_text, j["full_text"])
                    rmt_list_1_text.append(j["full_text"])
                    rmt_inner_list = [event["businessId"],
                                      j["full_text"],
                                      j["full_text_bbox"],
                                      event["id"],
                                      event["fileId"],
                                      datetime.datetime.utcnow(),
                                      event["userId"],
                                      datetime.datetime.utcnow(),
                                      event["userId"]]
                    rmt_list_1.append(tuple(rmt_inner_list))

                if "visit_date" in j and str(j["visit_date"]) not in uni_vd:
                    uni_vd.append(str(j["visit_date"]))

            rmt_insert_list = """INSERT into mentions_rel_text (business_id,
                                                                full_text,
                                                                full_text_bbox,
                                                                file_state_id,
                                                                file_id,
                                                                created_date,
                                                                created_by,
                                                                modified_date,
                                                                modified_by) VALUES %s RETURNING id, full_text"""

            results = execute_values(cur, rmt_insert_list,
                                     rmt_list_1, fetch=True)

            conn.commit()

            print("loaded REL MENTION FULL text and BBOX")

            # results = cur.fetchall()
            #
            # for result in results:
            #     print(result)

            mention_rel_text_id = None
            for j in master_list:

                # if there are more than 1 visit dates then put them here
                # otherwise update file_state table directly with the visit date
                visit_date = j["visit_date"] if 'visit_date' in j and len(uni_vd) > 1 else None

                # match_found = j["match_found"] if 'match_found' in j else None
                # overlap_entry = j["overlapping_entry"] if 'overlapping_entry' in j else None

                # if concepts are found then keep CUI and TUI else NONE
                tui, cui = None, None
                if "conceptAttributes" in j:
                    if j["conceptAttributes"]:
                        tui_cui = get_tui_cui(j["conceptAttributes"])
                        tui, cui = tui_cui[0], tui_cui[1]

                rect_coordinates = PGJson(j["rect_coordinates"]) if 'rect_coordinates' in j else None
                body_side = j["bodyside"] if "bodyside" in j else None
                relations = PGJson(j["relations"]) if j["relations"] else None
                polarity = j["polarity"] if "polarity" in j else None
                confidence = j["confidence"] if "confidence" in j else None

                for result in results:
                    if j["full_text"] == result[1]:
                        mention_rel_text_id = result[0]
                        break

                db_inner_list = [event["businessId"],
                                 j["begin"],
                                 j["end"],
                                 j["text"],
                                 # j["historyOf"],
                                 # j["subject"],
                                 polarity,
                                 confidence,
                                 # j["page_num"],
                                 j["page_number"],
                                 j["category"],
                                 visit_date,
                                 # match_found,
                                 tui,
                                 cui,
                                 rect_coordinates,
                                 event["userId"],
                                 datetime.datetime.utcnow(),
                                 event["userId"],
                                 datetime.datetime.utcnow(),
                                 event["userId"],
                                 event["bucket"],
                                 event["file_name"],
                                 event["id"],
                                 event["fileId"],
                                 mention_rel_text_id,
                                 body_side,
                                 relations]

                db_outer_list.append(tuple(db_inner_list))

            # load all mentions
            insert_list = """INSERT into sf_ctakes_mentions (business_id, 
                                                            "begin", 
                                                            "end", 
                                                            "text",  
                                                            polarity, 
                                                            confidence, 
                                                            page_number,
                                                            category,
                                                            visit_date, 
                                                            tui,
                                                            cui,
                                                            rect_coordinates, 
                                                            user_id, 
                                                            created_date, 
                                                            created_by, 
                                                            modified_date, 
                                                            modified_by,
                                                            bucket,
                                                            s3_file_dest,
                                                            file_state_id,
                                                            file_id,
                                                            mention_rel_text_id,
                                                            body_side,
                                                            relations) VALUES %s RETURNING id, 
                                                                                business_id,
                                                                                "begin", 
                                                                                "end",
                                                                                "text",
                                                                                page_number,
                                                                                category,
                                                                                visit_date,
                                                                                user_id,
                                                                                bucket,
                                                                                s3_file_dest,
                                                                                file_state_id,
                                                                                file_id                                                      
                                                                                """

            # print(cur.mogrify(insert_list, db_outer_list))
            db_annotations = execute_values(cur, insert_list, db_outer_list, fetch=True)

            # create relationships between annotations
            annotation_relation_to_db = []
            for annotation in master_list:
                try:
                    db_id_annotation = loop_annotations(db_annotations, annotation["begin"], annotation["end"], annotation["category"])
                    if db_id_annotation == 0:
                        raise ValueError(f"Received 0 id from DB for annotation: {annotation}. Proceeding to next annotation")
                    if "relations" in annotation:
                        for relation in annotation["relations"]:
                            if "frameSet" not in annotation:
                                if annotation["begin"] != relation["begin"] \
                                        and annotation["end"] != relation["end"] \
                                        and annotation["text"] != relation["text"] \
                                        and annotation["text"] != dummy_string \
                                        and relation["text"] != dummy_string:
                                    # print(annotation, relation)
                                    annot_category = get_annot_rel_type(cat, relation)

                                    # if annotation/relation category is not in our list then simply use whatever is in relation
                                    if annot_category is None:
                                        annot_category = relation["arg1Type"] if "arg1Type" in relation else relation["arg2Type"]
                                    db_id_rel = loop_annotations(db_annotations, relation["begin"], relation["end"], annot_category)
                                    annotation_relation_to_db.append((db_id_annotation, db_id_rel, relation["Relation_Category"]))
                except Exception as er:
                    print(er)

            relation_insert_query = """Insert into annotation_relationships (annotation_1_id, annotation_2_id,relation_Category 
                                        VALUES %s)"""
            execute_values(cur, relation_insert_query, annotation_relation_to_db)

            print("loaded MENTIONs")

            conn.commit()
            update_stmt = """UPDATE file_state SET mentions_start_instant = %s, 
                        mentions_processing_status = %s,
                        mentions_user_id = %s, 
                        mentions_completed_instant = %s, 
                        mentions_error_response = %s,
                        confirmed_visit_date = %s
                        where 
                            id = %s and business_id = %s and file_id = %s"""

            data = (start_time, 'fail' if exception_occurred else 'completed',
                    event["userId"],
                    datetime.datetime.utcnow(),
                    exception_for_db,
                    str(uni_vd[0]) if len(uni_vd) == 1 else None,
                    event["id"],
                    event["businessId"],
                    event["fileId"])

            print(cur.mogrify(update_stmt, data))
            cur.execute(update_stmt, data)
            conn.commit()

            print("updated file_state table with completion datetime and status")

        except Exception as e:
            traceback.print_exc(file=sys.stdout)

        finally:
            if conn:
                conn.close()
    else:
        print("exiting because it seems there was an exception in ctakes processing")
        print(event)


def get_annot_rel_type(cat, relation):
    for c in cat:
        for k, v in c.items():
            rel_type: str = relation["arg1Type"] if "arg1Type" in relation else relation["arg2Type"]
            if rel_type == k:
                return v


def loop_annotations(db_annotations, master_begin: int, master_end: int, master_category: str) -> int:
    for db_annotation in db_annotations:
        db_id: int = db_annotation[0]
        business_id: int = db_annotation[1]
        begin: int = db_annotation[2]
        end: int = db_annotation[3]
        text: str = db_annotation[4]
        page_number: int = db_annotation[5]
        category: str = db_annotation[6]
        visit_date: str = db_annotation[7]
        user_id: int = db_annotation[8]
        bucket: str = db_annotation[9]
        s3_file_dest: str = db_annotation[10]
        file_state_id: int = db_annotation[11]
        file_id: int = db_annotation[12]

        if master_begin == begin \
                and master_end == end \
                and master_category == category:
            return db_id

    return 0


if __name__ == "__main__":
    e = {'id': 524, 'businessId': 1, 'fileId': 62, 'file_name': '1/Case 14/62_MR_26.pdf',
         'splitterStatus': 'completed', 'userId': 2, 'extractFileName': '1/Case 14/62_MR_26_extract_text.txt',
         'bucket': 'starfizz-staging', 'debug': False, 'json_file': '1/Case 14/62_MR_26_extract_text.txt.json',
         'ctakes_exception': 'completed'}

    print(datetime.datetime.now())
    lambda_handler(e, None)
    print(datetime.datetime.now())
