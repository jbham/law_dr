import re


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
