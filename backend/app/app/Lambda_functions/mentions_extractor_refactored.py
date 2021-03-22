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
    body_region = []
    for local_d in local_payload:
        # new_payload = {}
        # new_payload["cui"] = local_d["cui"]
        # new_payload["tui"] = local_d["tui"]
        if "tui" in local_d:
            tui.append(local_d["tui"])

        if "cui" in local_d:
            cui.append(local_d["cui"])

        if "bodyRegion" in local_d:
            body_region += local_d["bodyRegion"]
    # using set and then list to ensure we are putting ONLY the unique values
    return PGJson(list(set(tui))), PGJson(list(set(cui))), PGJson(list(set(body_region)))


class ProcessAnnotations:
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

    def __init__(self, ctakes_response, doc, cur, conn, event):
        self.start_time = datetime.datetime.utcnow()
        self.ctakes_response = ctakes_response
        self.doc = doc
        self.cur = cur
        self.conn = conn
        self.event = event
        self.unique_begin_end = list()
        self.master_list_pre = list()
        self.master_list = list()

        self.word_r: str = ""
        self.found_visit_date = False

        self.chief_complaint_tracker = dict()
        self.cc_related_term_found = False

        self.history_of_present_illness = "(?:(?:CC\/HPI:)|(?:(?:HISTORY OF (?:THE )?(?:PRESENT |PHYSICAL )?(?:CONDITION|ILLNESS))(?: \(HPI(?:, PROBLEM BY PROBLEM)?\))*:?))"
        self.chief_complaint = "(?:CHIEF|PRIMARY).*COMPLAINTS?[\t ]*:"
        self.reason_for = "REASON.*FOR.*?(?:APPOINTMENT|EXAM)"

        self.hopi_regex = re.compile(self.history_of_present_illness, re.IGNORECASE | re.DOTALL)
        self.chief_complaints_regex = re.compile(self.chief_complaint, re.IGNORECASE | re.DOTALL)
        self.reason_for_regex = re.compile(self.reason_for, re.IGNORECASE | re.DOTALL)
        self.exception_occurred = False
        self.exception_for_db = ""

        self.uni_vd = []
        self.mention_db_results = None

        self.db_annotations = None

    def sort_master_list_pre(self, pop: bool = False, remove_overlapping: bool = False):
        sorted_master = sorted(self.master_list_pre, key=lambda k: k['begin'])

        if pop and remove_overlapping:
            obj_to_pop = self.find_overlapping_entries(sorted_master)
            self.master_list = [mlp for idx_mlp, mlp in enumerate(sorted_master) if idx_mlp not in obj_to_pop]
        else:
            self.master_list = sorted_master  # [mlp for idx_mlp, mlp in enumerate(sorted_master)]

    def run(self):
        self.pick_desired_annotations()
        self.sort_master_list_pre()
        text = ""
        text_running_length = len(text)
        pdf_text_mapping_list = []

        try:
            # loop through entire PDF text blocks and create a map with start, end, text, bbox, etc
            for i in range(0, len(self.doc)):
                pno: int = i
                page = self.doc[pno]
                got_text = page.getText("dict")

                for block_idx, nt in enumerate(got_text["blocks"]):
                    original_t = ""
                    if nt["type"] == 0:
                        for each_line in nt["lines"]:
                            for each_span in each_line["spans"]:
                                original_t += each_span["text"]

                        # if original_t ends with any number then add very unique dummy token
                        # so that CTAKES doesn't mess up in identifying measurements or date annotations
                        m = re.search(r'\d+$', original_t)
                        if m is not None:
                            original_t += f" {dummy_string}.\n"
                            # elif original_t.endswith("."):
                            #     original_t += "\n"
                        else:
                            original_t += "\n"

                        if u'\u2022' in original_t:
                            original_t = original_t.replace(u'\u2022', ".")

                        text_start = len(text)
                        text_end = text_start + len(original_t)

                        text = text + original_t

                        bbox = list(nt["bbox"])
                        bbox.append(page.rect.width)
                        bbox.append(page.rect.height)

                        pdf_text_mapping_dict = {"text_block": original_t,
                                                 "page_number": pno,
                                                 "bbox": bbox,
                                                 "text_block_length": len(original_t),
                                                 "begin": text_start,
                                                 "end": text_end}
                        pdf_text_mapping_list.append(pdf_text_mapping_dict)

                if not self.cc_related_term_found and text:
                    pdf_text_action = PDFTestRelatedAction(text,
                                                           self.hopi_regex,
                                                           self.chief_complaints_regex,
                                                           self.reason_for_regex)

                    hopi, cc, reason_for = pdf_text_action.section_finder_regex()

                    if hopi:
                        self.chief_complaint_tracker["start"] = hopi.span()[0]
                        self.chief_complaint_tracker["end"] = hopi.span()[1]
                        self.cc_related_term_found = True

                    if cc:
                        self.chief_complaint_tracker["start"] = cc.span()[0]
                        self.chief_complaint_tracker["end"] = cc.span()[1]
                        self.cc_related_term_found = True

                    if reason_for:
                        self.chief_complaint_tracker["start"] = reason_for.span()[0]
                        self.chief_complaint_tracker["end"] = reason_for.span()[1]
                        self.cc_related_term_found = True

            # now loop through master_list and attach bbox and full text block here:
            for idx_tbx, tbx in enumerate(self.master_list):

                already_found_text = False
                for i in range(len(pdf_text_mapping_list)):
                    if tbx["begin"] >= pdf_text_mapping_list[i]["begin"] \
                            and tbx["end"] <= pdf_text_mapping_list[i]["end"]:
                        self.master_list[idx_tbx]["full_text"] = pdf_text_mapping_list[i]["text_block"]
                        self.master_list[idx_tbx]["full_text_bbox"] = str(pdf_text_mapping_list[i]["bbox"])
                        self.master_list[idx_tbx]["page_number"] = pdf_text_mapping_list[i]["page_number"]

                        already_found_text = True

                        # if tbx["text"] in ['teat', 'Cr', 'Th', 'ROB']:
                        #     print("test")

                    # ctakes may find important terms which fall into previous and current block
                    # lets handle that scenario here:
                    # split tbx["text"] based on newline char
                    if not already_found_text:
                        txt_to_prcs = str(tbx["text"])
                        if '\n' in txt_to_prcs:
                            split = str(tbx["text"]).split("\n")
                            # first part of the text is in previous block and second part is in current block
                            if split[0] in pdf_text_mapping_list[i - 1]["text_block"] and split[1] in pdf_text_mapping_list[i]["text_block"]:
                                self.master_list[idx_tbx]["full_text"] = pdf_text_mapping_list[i]["text_block"]
                                self.master_list[idx_tbx]["full_text_bbox"] = str(pdf_text_mapping_list[i]["bbox"])
                                self.master_list[idx_tbx]["page_number"] = pdf_text_mapping_list[i]["page_number"]

                    if tbx["end"] < pdf_text_mapping_list[i]["end"]:
                        break

            self.word_r = text
            self.find_visit_dates()
            self.mention_related_text()
            self.load_annotations_in_db()
            self.process_load_annotation_relations()
        except Exception as e:
            print(e)
            self.exception_occurred = True
            self.exception_for_db = traceback.print_exc(file=sys.stdout)

        # we want to update the DB tables after everything has been processes or error'd out
        self.update_file_state_table()

    def find_visit_dates(self):
        for li, l in enumerate(self.master_list):
            # only check for DATES which SHOW UP before Chief Complaint
            if not self.found_visit_date:
                # # print(li, l["text"])
                date_f = str(l["text"])
                try:
                    # if we have a valid date then we can work on further validations
                    if self.is_year_in_date(date_f):

                        # get 20 characters from left and 40 characters
                        # from the starting point of the string
                        # neighboring_words = \
                        #     word_r[int(word_r.index(date_f)) - 20:int(word_r.index(date_f)) + 40]
                        neighboring_words = self.word_r[int(l["begin"]) - 20:int(l["begin"]) + 40]

                        leave_nvdl_loop = self.is_dob_date(neighboring_words)

                        if leave_nvdl_loop:
                            continue

                        self.is_visit_date_label(neighboring_words)

                        # we have reached until CHIEF complaint but did not find visit date
                        # so mark every date, which is before Chief Complaint, as visit date
                        if l["begin"] <= self.chief_complaint_tracker["start"] and not self.found_visit_date:
                            self.master_list[li]["visit_date"] = date_f

                        # sometimes SOC dates would show up after Chief Complaint
                        # ensure that we mark a date as VISIT date ONLY if they are listed in the list of possible
                        # VISIT DATE lables
                        elif l["begin"] >= self.chief_complaint_tracker["start"] and self.found_visit_date:
                            self.master_list[li]["visit_date"] = date_f

                        # we are either above or below CHIEF COMPLAINT and we found the exact VISIT date we are
                        # looking for. "is_visit_date_label" function negates every other date, which may have been
                        # marked as VISIT date
                        elif self.found_visit_date:
                            self.master_list[li]["visit_date"] = date_f

                except Exception as x:
                    print(x)

    def pick_desired_annotations(self):
        for c in self.cat:
            for k, v in c.items():
                if k in self.ctakes_response:
                    for k1 in self.ctakes_response[k]:

                        # adding three conditions below (took out first condition so that all annotation types can flow through
                        #                   because later in the process when creating relations between annotations, it wouldn't find
                        #                   removed annotation and won't create relation):
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
                                        k1["type"] = "Predicates"
                                        self.master_list_pre.append(k1)
                                        self.unique_begin_end.append(int(k1["begin"] + k1["end"]))
                                else:
                                    # k1["category"] = str(v)
                                    self.master_list_pre.append(k1)
                                    self.unique_begin_end.append(int(k1["begin"] + k1["end"]))

        self.relation_to_annotation()

    def relation_to_annotation(self):
        new_annotation_to_be_added = list()
        for index, annotation in enumerate(self.master_list_pre):
            try:
                if "relations" in annotation and annotation["type"] != "Predicates":
                    # loop through master_list_pre again
                    for relation in annotation["relations"]:
                        rel_type = relation["arg1Type"] if "arg1Type" in relation else relation["arg2Type"]
                        match_found = False
                        for annotation2 in self.master_list_pre:
                            if annotation2["type"] != "Predicates":
                                if relation["begin"] == annotation2["begin"] and \
                                        relation["end"] == annotation2["end"] and \
                                        rel_type == annotation2["type"]:  # or #rel_type == annotation2["category"]
                                    match_found = True
                        if not match_found:
                            d = {"begin": relation["begin"],
                                 "end": relation["end"],
                                 "text": relation["text"],
                                 "type": rel_type,
                                 "conceptAttributes": relation["rel_concept"] if "rel_concept" in relation else None}
                            new_annotation_to_be_added.append(d)
            except Exception as e:
                print(e)

        self.master_list_pre += new_annotation_to_be_added

    def find_overlapping_entries(self, full_list):
        local_idx_to_pop = []

        for idxl, ltr in enumerate(full_list):
            for li, lw in enumerate(full_list):
                if idxl != li and ltr["begin"] <= lw["begin"] and ltr["end"] >= lw["end"]:
                    local_idx_to_pop.append(li)

        return local_idx_to_pop

    def between_function(self, v_search, page_detail_list_func):
        # TODO: start needs in the same page and end needs to be on the same page as well
        # it possibles that half of the word is in one page and other half is on the next page

        for index_local, page_local in enumerate(page_detail_list_func):
            if page_local["starts_at"] <= v_search <= page_local["running_length"]:
                return index_local

    def omit_if_before_cp(self, end):
        return False if int(end) < cp_end else True

    def is_year_in_date(self, local_date_f):
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

    def is_dob_date(self, local_neighboring_words):
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

    def is_visit_date_label(self, local_neighboring_words):
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
                self.found_visit_date = True

                # once we have found our visit date then we should loop through
                # dateAnnotations and unmark/remove any other visit date that we may have found
                for inner_idx, inner_agg_list in enumerate(self.master_list):
                    # if inner_agg_list["category"] == "DateAnnotation":
                    # new_agg_all_list.append(inner_agg_list)
                    if "visit_date" in inner_agg_list:
                        del inner_agg_list["visit_date"]

    def mention_related_text(self):
        rmt_list_1_text = []
        rmt_list_1 = []
        # unique visit dates

        for idx, j in enumerate(self.master_list):
            # print(idx, j)
            if "full_text" not in j:
                print("test")
            if str(j["full_text"]) not in rmt_list_1_text:
                # print(rmt_list_1_text, j["full_text"])
                rmt_list_1_text.append(j["full_text"])
                rmt_inner_list = [self.event["businessId"],
                                  j["full_text"],
                                  j["full_text_bbox"],
                                  self.event["id"],
                                  self.event["fileId"],
                                  datetime.datetime.utcnow(),
                                  self.event["userId"],
                                  datetime.datetime.utcnow(),
                                  self.event["userId"]]
                rmt_list_1.append(tuple(rmt_inner_list))

            if "visit_date" in j and str(j["visit_date"]) not in self.uni_vd:
                self.uni_vd.append(str(j["visit_date"]))

        rmt_insert_list = """INSERT into mentions_rel_text (business_id,
                                                            full_text,
                                                            full_text_bbox,
                                                            file_state_id,
                                                            file_id,
                                                            created_date,
                                                            created_by,
                                                            modified_date,
                                                            modified_by) VALUES %s RETURNING id, full_text"""

        self.mention_db_results = execute_values(self.cur, rmt_insert_list,
                                                 rmt_list_1, fetch=True)

        self.conn.commit()

    def load_annotations_in_db(self):
        try:
            db_outer_list = []
            mention_rel_text_id = None
            for j in self.master_list:

                # if there are more than 1 visit dates then put them here
                # otherwise update file_state table directly with the visit date
                visit_date = j["visit_date"] if 'visit_date' in j and len(self.uni_vd) > 1 else None

                # match_found = j["match_found"] if 'match_found' in j else None
                # overlap_entry = j["overlapping_entry"] if 'overlapping_entry' in j else None

                # if concepts are found then keep CUI, TUI, else NONE
                tui, cui, body_region = None, None, None
                if "conceptAttributes" in j:
                    if j["conceptAttributes"]:
                        tcbr = get_tui_cui(j["conceptAttributes"])
                        tui, cui, body_region = tcbr[0], tcbr[1], tcbr[2]

                rect_coordinates = PGJson(j["rect_coordinates"]) if 'rect_coordinates' in j else None
                body_side = j["bodyside"] if "bodyside" in j else None

                # only load relations for Predicates/Relations because of others they are going into annotation_relationship table
                relations = PGJson(j["relations"]) if "relations" in j and j["type"] == "Predicates" else None
                polarity = j["polarity"] if "polarity" in j else None
                confidence = j["confidence"] if "confidence" in j else None

                for result in self.mention_db_results:
                    if j["full_text"] == result[1]:
                        mention_rel_text_id = result[0]
                        break

                db_inner_list = [self.event["businessId"],
                                 j["begin"],
                                 j["end"],
                                 j["text"],
                                 # j["historyOf"],
                                 # j["subject"],
                                 polarity,
                                 confidence,
                                 # j["page_num"],
                                 j["page_number"],
                                 visit_date,
                                 # match_found,
                                 tui,
                                 cui,
                                 rect_coordinates,
                                 self.event["userId"],
                                 datetime.datetime.utcnow(),
                                 self.event["userId"],
                                 datetime.datetime.utcnow(),
                                 self.event["userId"],
                                 self.event["bucket"],
                                 self.event["file_name"],
                                 self.event["id"],
                                 self.event["fileId"],
                                 mention_rel_text_id,
                                 body_side,
                                 body_region,
                                 relations,
                                 j["type"]]

                db_outer_list.append(tuple(db_inner_list))

            # load all mentions
            insert_list = """INSERT into sf_ctakes_mentions (business_id, 
                                                                        "begin", 
                                                                        "end", 
                                                                        "text",  
                                                                        polarity, 
                                                                        confidence, 
                                                                        page_number,
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
                                                                        body_region,
                                                                        relations,
                                                                        annotation_type) VALUES %s RETURNING id, 
                                                                                            business_id,
                                                                                            "begin", 
                                                                                            "end",
                                                                                            "text",
                                                                                            page_number,
                                                                                            annotation_type,
                                                                                            visit_date,
                                                                                            user_id,
                                                                                            bucket,
                                                                                            s3_file_dest,
                                                                                            file_state_id,
                                                                                            file_id                                                      
                                                                                            """

            # print(cur.mogrify(insert_list, db_outer_list))
            self.db_annotations = execute_values(self.cur, insert_list, db_outer_list, fetch=True)
            self.conn.commit()
        except Exception as er:
            print(er)
            self.exception_occurred = True
            self.exception_for_db = traceback.print_exc(file=sys.stdout)

    def process_load_annotation_relations(self):
        annotation_relation_to_db = []
        unique_annotations_relations = []
        for annotation in self.master_list:
            try:
                db_id_annotation = self.loop_annotations(annotation["begin"], annotation["end"], annotation["type"])
                if db_id_annotation == 0:
                    raise ValueError(f"Received 0 id from DB for annotation: {annotation}. Proceeding to next annotation")
                if "relations" in annotation:
                    for relation in annotation["relations"]:
                        if "frameSet" not in annotation:
                            if annotation["begin"] + annotation["end"] != relation["begin"] + relation["end"] \
                                    and annotation["text"] != dummy_string \
                                    and relation["text"] != dummy_string:
                                annot_type = relation["arg1Type"] if "arg1Type" in relation else relation["arg2Type"]
                                db_id_rel = self.loop_annotations(relation["begin"], relation["end"], annot_type)

                                # below check is to ensure we are ONLY loading unique relations
                                if f"{db_id_annotation}-{db_id_rel}" not in unique_annotations_relations:
                                    annotation_relation_to_db.append((self.event["businessId"], db_id_annotation, db_id_rel,
                                                                      relation["Relation_Category"], datetime.datetime.utcnow(),
                                                                      datetime.datetime.utcnow()))
                                    unique_annotations_relations.append(f"{db_id_annotation}-{db_id_rel}")
            except Exception as er:
                print(er)
                self.exception_occurred = True
                self.exception_for_db = traceback.print_exc(file=sys.stdout)

        try:
            relation_insert_query = """Insert into annotation_relationships (business_id, annotation_1_id, annotation_2_id,
                                                                            "relation_type", created_date, modified_date)
                                                                            VALUES %s"""

            # print(self.cur.mogrify(relation_insert_query, annotation_relation_to_db))
            execute_values(self.cur, relation_insert_query, annotation_relation_to_db)
            self.conn.commit()
        except Exception as e:
            print(e)
            self.exception_occurred = True
            self.exception_for_db = traceback.print_exc(file=sys.stdout)

    def loop_annotations(self, master_begin: int, master_end: int, master_type: str) -> int:
        for db_annotation in self.db_annotations:
            db_id: int = db_annotation[0]
            begin: int = db_annotation[2]
            end: int = db_annotation[3]
            type: str = db_annotation[6]

            if master_begin == begin \
                    and master_end == end \
                    and master_type == type:
                return db_id

        return 0

    def update_file_state_table(self):
        try:
            update_stmt = """UPDATE file_state SET mentions_start_instant = %s, 
                                    mentions_processing_status = %s,
                                    mentions_user_id = %s, 
                                    mentions_completed_instant = %s, 
                                    mentions_error_response = %s,
                                    confirmed_visit_date = %s
                                    where 
                                        id = %s and business_id = %s and file_id = %s"""

            data = (self.start_time, 'fail' if self.exception_occurred else 'completed',
                    self.event["userId"],
                    datetime.datetime.utcnow(),
                    self.exception_for_db,
                    str(self.uni_vd[0]) if len(self.uni_vd) == 1 else None,
                    self.event["id"],
                    self.event["businessId"],
                    self.event["fileId"])

            # print(self.cur.mogrify(update_stmt, data))
            self.cur.execute(update_stmt, data)
            self.conn.commit()
        except Exception as e:
            print(f"Exception from update_file_state_table : \n {e}")
            print(f"Full stack trace: \n{traceback.print_exc(file=sys.stdout)}")


def lambda_handler(event, context):
    # start_time = datetime.datetime.utcnow()
    print(event)
    if str(event["ctakes_exception"]) == 'completed':
        s3 = boto3.client('s3')
        try:
            s3_object = s3.get_object(Bucket=event["bucket"], Key=event["file_name"])
            doc = fitz.open(None, s3_object["Body"].read(), "pdf")
            s3_object = s3.get_object(Bucket=event["bucket"], Key=event["json_file"])

            s = s3_object["Body"].read()
            conn = psycopg2.connect(
                "dbname='starfizz' user='starfizz' host='starfizz.cqjzxqvvjp0y.us-west-2.rds.amazonaws.com' password='starfizz'")

            cur = conn.cursor(cursor_factory=DictCursor)
            process_annotations = ProcessAnnotations(json.loads(s), doc, cur, conn, event)
            process_annotations.run()

        except Exception as e:
            print(f"Exception from lambda_handler : \n {e}")
            print(f"Full stack trace: \n{traceback.print_exc(file=sys.stdout)}")
        finally:
            doc.close()
    else:
        print("Document will not be processes because event[\"ctakes_exception\"] == 'completed'. See event details above")


if __name__ == "__main__":
    e = {'id': 484, 'businessId': 1, 'fileId': 57, 'file_name': '1/Case 14/57_MR_1.pdf',
         'splitterStatus': 'completed', 'userId': 2, 'extractFileName': '1/Case 14/57_MR_1_extract_text.txt',
         'bucket': 'starfizz-staging', 'debug': False, 'json_file': '1/Case 14/57_MR_1_extract_text.txt.json',
         'ctakes_exception': 'completed'}

    print(datetime.datetime.now())
    lambda_handler(e, None)
    print(datetime.datetime.now())
