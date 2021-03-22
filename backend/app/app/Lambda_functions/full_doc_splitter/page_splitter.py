import re
import traceback
import os
import fitz
import datetime


class PDFPageSplitter:

    def __init__(self, doc_file_name, start, end, s3_object, doc, event_obj, text_per_page, new_doc_file_name=None,
                 new_extract_file_name=None):
        self.event_for_splitter = event_obj
        self.doc_file_name = doc_file_name
        self.start = start
        self.end = end
        self.new_doc_file_name = new_doc_file_name
        self.new_extract_file_name = new_extract_file_name
        self.doc = doc
        self.text_per_page = text_per_page
        self.new_doc = None
        # self.s3 = boto3.client('s3', aws_access_key_id=,AWS_ACCESS_KEY_DECRYPTED
        #                   aws_secret_access_key=AWS_SECRET_KEY_DECRYPTED)
        self.s3 = s3_object
        self.s3_upload_resp = None
        self.s3_upload_extract_text_resp = None
        self.start_time = datetime.datetime.utcnow()
        self.exception_occurred = False
        self.splitter_generic_exception = None

    def split_pages(self):
        self.new_doc.insertPDF(self.doc,  # cannot be the same object as new_doc
                               from_page=self.start,  # first page to copy, default: 0
                               to_page=self.end,  # last page to copy, default: last page
                               links=True)  # also copy links & annotations

    def perform_regex(self, s):
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

    def open_doc_docs(self):
        """
        :return:None
        """
        # self.doc = fitz.open(self.doc_file_name)
        self.new_doc = fitz.open()

    def save_new_doc(self):
        """

        :return: None
        """
        # stream the bytes to s3 directly ... love it!
        try:
            self.s3_upload_resp = self.s3.put_object(
                Bucket="starfizz-staging",
                Body=self.new_doc.write(),
                Key=self.new_doc_file_name,
                Metadata=self.event_for_splitter
            )
        except Exception as e:
            self.s3_upload_resp = str(e)

        text = str()

        # # page_detail_list = []
        #
        # # chief_complaint = dict()
        #
        # # txt = 'Chief Complaints'
        #
        # # re1 = '(Chief)'  # Variable Name 1
        # # re2 = '.*?'  # Non-greedy match on filler
        # # re3 = '(Complaint)'  # Variable Name 2
        #
        # for i in range(0, len(self.new_doc)):
        #     page_detail = {}
        #     pno = i
        #
        #     page = self.new_doc[pno]
        #
        #     got_text = page.getText("dict")
        #     t = extract_text_blocks(got_text)
        #
        #     # original_t = ""
        #     # for nt in got_text["blocks"]:
        #     #     if nt["type"] == 0:
        #     #         for each_line in nt["lines"]:
        #     #             for each_span in each_line["spans"]:
        #     #                 original_t += each_span["text"]
        #     #
        #     #         # if original_t ends with any number then add some string with newline character
        #     #         # so that CTAKES doesn't mess up in identifying measurements or date annotations
        #     #         m = re.search(r'\d+$', original_t)
        #     #         if m is not None:
        #     #             original_t += " SamKamJas.\n"
        #     #             # elif original_t.endswith("."):
        #     #             #     original_t += "\n"
        #     #         else:
        #     #             original_t += "\n"
        #     #
        #     #         # remove bullet list character
        #     #         if u'\u2022' in original_t:
        #     #             original_t = original_t.replace(u'\u2022', ".")
        #     #
        #     #         original_t_len = len(original_t)
        #
        #     # print(original_t)
        #
        #     # t = self.perform_regex(original_t)
        #
        #     # t = original_t
        #
        #     # rg = re.compile(re1 + re2 + re3, re.IGNORECASE | re.DOTALL)
        #     # m = rg.search(t)
        #     # if m:
        #     #     chief_complaint["start"] = m.span()[0]
        #     #     chief_complaint["end"] = cp_end = m.span()[1]
        #     #     var1 = m.group(1)
        #     #     var2 = m.group(2)
        #     #     # # print("(" + var1 + ")" + "(" + var2 + ")" + "\n")
        #
        #     # page_detail["page_number"] = pno
        #     # if page_detail_list:
        #     #     previous_page_detail = page_detail_list[i - 1]
        #     #     page_detail["starts_at"] = previous_page_detail["running_length"] + 1
        #     #     page_detail["page_length"] = len(t)
        #     #     page_detail["running_length"] = previous_page_detail["running_length"] + len(t)
        #     #     # page_detail["text"] = t
        #     # else:
        #     #     page_detail["starts_at"] = 0
        #     #     page_detail["page_length"] = len(t)
        #     #     page_detail["running_length"] = len(t)
        #     #     # page_detail["text"] = t
        #     #     self.event_for_splitter["first_page_length"] = str(len(t))
        #
        #     # page_detail_list.append(page_detail)
        #     text = text + t

        text_list: list = []
        for i in range(self.start, self.end + 1):
            text_list.append(self.text_per_page[i])

        text = ''.join(text_list)

        # stream the bytes to s3 directly ... love it!
        try:
            self.s3_upload_extract_text_resp = self.s3.put_object(
                Bucket="starfizz-staging",
                Body=bytearray(text.encode()),
                Key=self.new_extract_file_name,
                Metadata=self.event_for_splitter
            )
            print(str(self.s3_upload_extract_text_resp))
            print(f"Uploaded extract file: {self.new_extract_file_name}")
        except Exception as e:
            print(f"Exception occurred while running PDFPageSplitter: \n {traceback.print_exc()}")
            print(e)
            self.s3_upload_extract_text_resp = str(e)

        print("---------------------------------------------------------------")

    def close_doc(self, which_doc=None):
        """
        :param which_doc: valid values are "SOURCE" or "DESTINATION"
        :return: None
        """

        # if none is specified then close both docs
        # otherwise close the one specified
        if which_doc is None:
            self.doc.close()
            self.new_doc.close()
        elif str(which_doc).upper() == 'SOURCE':
            self.doc.close()
        elif str(which_doc).upper() == 'DESTINATION':
            self.new_doc.close()

    def run(self):
        try:

            print(f"Total number of pages: {abs(self.start - self.end)}")
            print(f"Total number of pages: start: {self.start} -- end: {self.end}")

            if int(abs(self.start - self.end)) > 10:
                # raise Exception(f"Max pages per single  document is 10. But, {abs(self.start - self.end)} were found")
                print("More than 10 pages found")

            self.open_doc_docs()
            self.split_pages()
            self.save_new_doc()

        except Exception as e:
            print(f"Exception occurred while running PDFPageSplitter: \n {traceback.print_exc()}")
            self.exception_occurred = True
            self.splitter_generic_exception = str(e)

        finally:

            if self.new_doc:
                self.close_doc(which_doc="DESTINATION")

            return (int(self.event_for_splitter['business_id']),
                    int(self.event_for_splitter['file_item_id']),
                    self.new_doc_file_name,
                    self.start_time,
                    datetime.datetime.utcnow(),
                    'fail' if self.exception_occurred else 'completed',
                    int(self.event_for_splitter['user_id']),
                    str(self.s3_upload_resp),
                    datetime.datetime.utcnow(),
                    str(self.s3_upload_extract_text_resp),
                    self.new_extract_file_name,
                    self.splitter_generic_exception if self.exception_occurred else None,
                    'UNASSIGNED',
                    int(self.event_for_splitter['user_id']),
                    abs(self.start - self.end) + 1)



