from typing import Dict
import re
import traceback
import sys
import json
import fitz
from page_splitter import PDFPageSplitter
from pdf_text_related_action import PDFTestRelatedAction
from extract_text_blocks import extract_text_blocks
from base64 import b64decode
import os
import boto3
import psycopg2
from psycopg2.extras import execute_values
import datetime


# AWS_ACCESS_KEY_ENCRYPTED = os.environ['aws_access_key_id']
# # Decrypt code should run once and variables stored outside of the function
# # handler so that these are decrypted once per container
# AWS_ACCESS_KEY_DECRYPTED = boto3.client('kms').decrypt(CiphertextBlob=b64decode(AWS_ACCESS_KEY_ENCRYPTED))['Plaintext']


# AWS_SECRET_KEY_ENCRYPTED = os.environ['aws_secret_access_key']
# # Decrypt code should run once and variables stored outside of the function
# # handler so that these are decrypted once per container
# AWS_SECRET_KEY_DECRYPTED = boto3.client('kms').decrypt(CiphertextBlob=b64decode(AWS_SECRET_KEY_ENCRYPTED))['Plaintext']


class FullDocSplitter:
    chief_complaints = ["Chief Complaint", "Chief Complaints", "CC"]

    def __init__(self, event_details, s3_object):
        self.thisEvent = event_details
        self.doc_file_name = event_details["s3_location"]
        self.s3 = s3_object
        self.doc = None
        self.start = int()
        self.end = int()
        self.first_cc = False
        self.mr_counter = 1
        self.details_for_db = []

        history_of_present_illness = "(?:(?:CC\/HPI:)|(?:(?:HISTORY OF (?:THE )?(?:PRESENT |PHYSICAL )?(?:CONDITION|ILLNESS))(?: \(HPI(?:, PROBLEM BY PROBLEM)?\))*:?))"
        chief_complaint = "(?:CHIEF|PRIMARY).*COMPLAINTS?[\t ]*:"
        reason_for = "REASON.*FOR.*?(?:APPOINTMENT|EXAM)"

        self.hopi_regex = re.compile(history_of_present_illness, re.IGNORECASE | re.DOTALL)
        self.chief_complaints_regex = re.compile(chief_complaint, re.IGNORECASE | re.DOTALL)
        self.reason_for_regex = re.compile(reason_for, re.IGNORECASE | re.DOTALL)

    def open_doc(self):
        local_object = self.s3.get_object(Bucket=self.thisEvent["bucket"], Key=self.doc_file_name)
        self.doc = fitz.open(None, local_object["Body"].read(), "pdf")

    def close_doc(self):
        self.doc.close()

    def run(self):
        # open the doc
        print("Opening doc..")

        text_per_page: Dict = {}

        try:

            self.open_doc()

            # print("doc opened. looping through pages....")

            # loop through the doc
            for pno in range(0, len(self.doc)):

                # print("just pno", pno)

                # text = str(self.doc.getPageText(pno))
                page = self.doc[pno]
                got_text = page.getText("dict")
                text = extract_text_blocks(got_text)

                text_per_page[pno] = text

                pdf_text_action = PDFTestRelatedAction(text,
                                                       self.hopi_regex,
                                                       self.chief_complaints_regex,
                                                       self.reason_for_regex)
                # pdf_text_action.clean_text()

                # cc = pdf_text_action.chief_complaint()
                # print("cc", cc, pno, len(self.doc))

                hopi, cc, reason_for = pdf_text_action.section_finder_regex()

                if cc or hopi or reason_for:
                    if not self.first_cc:
                        self.start = pno
                        self.first_cc = True
                        # print("if")
                    else:
                        # print("else")
                        self.end = pno - 1
                        new_doc_file = self.doc_file_name.replace(".pdf", f"_MR_{self.mr_counter}.pdf")
                        new_extract_file_name = self.doc_file_name.replace(".pdf",
                                                                           f"_MR_{self.mr_counter}_extract_text.txt")
                        print("new_doc_file", new_doc_file)
                        # split pages

                        # if we have more than 10 pages per document then we need split them in 5 pages per document
                        # this would make CTAKES process this document
                        total = int(abs(self.start - self.end))

                        # for ik in range(0,6):
                        #
                        # if total > 10:
                        #     for i in range(0,math.ceil(total/5)):

                        pdf_ps = PDFPageSplitter(self.doc_file_name,
                                                 self.start,
                                                 self.end,
                                                 self.s3,
                                                 self.doc,
                                                 self.thisEvent,
                                                 text_per_page,
                                                 new_doc_file,
                                                 new_extract_file_name)

                        each_file_details = pdf_ps.run()
                        self.details_for_db.append(each_file_details)

                        self.mr_counter += 1

                        # set new CC starting page number
                        self.start = pno

                else:
                    if pno == (len(self.doc) - 1):
                        # print("Last else part...", pno, len(self.doc), len(self.doc) - 1, self.start, self.end)
                        self.end = pno
                        new_doc_file = self.doc_file_name.replace(".pdf", f"_MR_{self.mr_counter}.pdf")
                        new_extract_file_name = self.doc_file_name.replace(".pdf",
                                                                           f"_MR_{self.mr_counter}_extract_text.txt")
                        pdf_ps = PDFPageSplitter(self.doc_file_name,
                                                 self.start,
                                                 self.end,
                                                 self.s3,
                                                 self.doc,
                                                 self.thisEvent,
                                                 text_per_page,
                                                 new_doc_file,
                                                 new_extract_file_name)

                        each_file_details = pdf_ps.run()
                        self.details_for_db.append(each_file_details)

        except Exception as e:
            print(f"Exception occurred from lambda_function.py: {e}")
            traceback.print_exc(file=sys.stdout)
        finally:
            print("closing doc..")
            self.close_doc()
            print("Doc closed")

            try:
                conn = psycopg2.connect(
                    "dbname='starfizz' user='starfizz' host='starfizz.cfczkxmaisbd.us-west-2.rds.amazonaws.com' password='starfizz'")
                print("Connected successfully")
                cur = conn.cursor()

                execute_values(cur, """INSERT INTO file_state (business_id, 
                                                            file_id, 
                                                            new_file_name, 
                                                            splitter_start_instant, 
                                                            splitter_completed_instant, 
                                                            splitter_status, 
                                                            splitter_user_id, 
                                                            splitter_s3_upload_resp, 
                                                            last_modified_instant, 
                                                            extract_text_s3_upload_resp, 
                                                            extract_file_name,
                                                            splitter_generic_exception,
                                                            ctakes_server_status,
                                                            last_modified_by,
                                                            total_split_pages) 
                                            VALUES %s 
                                            RETURNING id, 
                                                        business_id, 
                                                        file_id, 
                                                        new_file_name, 
                                                        splitter_status,
                                                        splitter_user_id,
                                                        extract_file_name""", self.details_for_db)

                conn.commit()

            except Exception as e:
                print("I am unable to connect to the database")
                print(str(e))

            main_list = list()

            try:
                results = cur.fetchall()

                for result in results:
                    payload = dict()

                    # {
                    # 	"id": 4,
                    # 	"businessId": 1,
                    # 	"bucket": "starfizz-staging",
                    # 	"fileId":2,
                    # 	"userId": 4,
                    # 	"splitterStatus" : "completed",
                    # 	"extractFileName": "1/Case 1/2_MR_1_extract_text.txt",

                    # 	"file_name" : "1/Case 1/2_MR_1.pdf",
                    # 	"debug": false
                    # }

                    payload['id'] = result[0]
                    payload['businessId'] = result[1]
                    payload['fileId'] = result[2]
                    payload['file_name'] = result[3]
                    payload['splitterStatus'] = result[4]
                    payload['userId'] = result[5]
                    payload['extractFileName'] = result[6]
                    payload["bucket"] = self.thisEvent["bucket"]
                    payload['debug'] = False

                    print("Payload 1", payload)
                    main_list.append(payload)

            except Exception as e:
                print(str(e))
                print(f"Exception occurred while processing fetched records: \n {traceback.print_exc()}")

            print(json.dumps(main_list))

            client = boto3.client('sqs', aws_access_key_id=self.thisEvent['aws_access_key_id'],
                                  aws_secret_access_key=self.thisEvent['aws_secret_access_key'])

            sqs_response = client.send_message(
                QueueUrl='https://sqs.us-west-2.amazonaws.com/752989888451/cfizz_msg_bus',
                MessageBody='{"TYPE":"onNewDocArrival"}',
                DelaySeconds=5
            )

            print(sqs_response)

            # results = cur.fetchall()

            # for result in results:
            #     payload = {}
            #     payload['id'] = result[0]
            #     payload['business_id'] = result[1]
            #     payload['parent_file_id'] = result[2]
            #     payload['new_file_name'] = result[3]
            #     payload['splitter_status'] = result[4]
            #     payload['aws_access_key_id'] = self.thisEvent['aws_access_key_id']
            #     payload['aws_secret_access_key'] = self.thisEvent['aws_secret_access_key']

            #     lambda_client = boto3.client('lambda', aws_access_key_id=self.thisEvent['aws_access_key_id'], aws_secret_access_key=self.thisEvent['aws_secret_access_key'])

            #     res = lambda_client.invoke(FunctionName='arn:aws:lambda:us-west-2:752989888451:function:extract_text',
            #                               InvocationType='Event',
            #                               Payload=json.dumps(payload))

            #     print(res)

            #     s = str(res).replace("'",'"')

            #     sql = f"UPDATE file_state SET splitter_to_extract_text_hand_off_resp = '{s}'," \
            #         f" last_modified_instant = '{str(datetime.datetime.utcnow())}' WHERE id = {result[0]} "

            #     print(sql)

            #     cur.execute(sql)

            #     conn.commit()

            print("Closing DB connection")
            conn.close()
            print("Db connection closed")


def lambda_handler(event, context):
    # TODO implement
    print(fitz.__doc__, "\n")
    print(event)

    s3 = boto3.client('s3', aws_access_key_id=event['aws_access_key_id'],
                      aws_secret_access_key=event['aws_secret_access_key'])

    FullDocSplitter(event, s3).run()

    # if event:
    #     file_obj = event['Records'][0]
    #     filename = file_obj['s3']['object']['key']
    #     print(f"filename: {filename}")

    #     #object = s3.get_object(Bucket="test-fizz", Key=filename)

    #     FullDocSplitter(filename, s3).run()


if __name__ == "__main__":
    event = {'business_id': '2', 'user_id': '2', 'file_item_id': '113', 's3_location': '2/Case 4/116_MR_1.pdf',
             'splitFileTerm': '', 'aws_access_key_id': 'AKIAIJEQARD7JIT4ETGA',
             'aws_secret_access_key': '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', 'bucket': 'starfizz-staging'}

    lambda_handler(event, None)
