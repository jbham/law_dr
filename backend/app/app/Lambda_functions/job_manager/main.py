import traceback
import os
import sys
import logging
import datetime
import traceback
import time
import boto3
import psycopg2
import json
import requests
from app.core.config import (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
                             AWS_UPLOAD_BUCKET, AWS_UPLOAD_REGION, AWS_ROLE_ARN, AWS_ROLE_SESSION_NAME)

logger = logging.getLogger()

logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-7s %(threadName)-15s %(message)s',
                    level=logging.DEBUG)


class JobManager:

    POSTGRES_SERVER, POSTGRES_PORT = os.getenv('POSTGRES_SERVER').split(":")

    connection_string = f"dbname='starfizz' user='{os.getenv('POSTGRES_USER')}' host='{POSTGRES_SERVER}' password='{os.getenv('POSTGRES_PASSWORD')}' port='{POSTGRES_PORT}'"

    def __init__(self, event):

        self.type = event["TYPE"]
        self.newDocArrivalSignal = True if self.type == "onNewDocArrival" else False
        self.conn = psycopg2.connect(self.connection_string)
        self.cur = self.conn.cursor()
        self.event = event
        self.number_of_processes_available = \
            int(self.event["AVAILABLE_CORES"]) if "AVAILABLE_CORES" in self.event else 0

        self.check_and_acquire_lock()

        self.last_biz_id = int()
        self.main_biz_list = list()

        self.right_list = list()
        self.left_list = list()
        self.status_code_403 = 0
        self.status_code_500 = 0

    def close_db_conn(self):
        self.conn.close()

    def get_distinct_biz_ids(self):
        try:
            query = """select
                            business_id
                        from
                            public.file_state
                        where
                            ctakes_server_status = 'UNASSIGNED'
                        order by
                            last_modified_instant asc;"""

            self.cur.execute(query)
            rows = self.cur.fetchall()
            for row in rows:
                if row[0] not in self.main_biz_list:
                    self.main_biz_list.append(row[0])

            print(self.main_biz_list)

        except Exception as e:
            print(f"Exception occurred while checking lock: {e}")
            print(traceback.format_exc())
            self.close_db_conn()

    # check if another JobManager instance is trying to allocate resources
    # if yes then wait to continue assigning resources
    # acquire lock so other JobManagers wait
    def check_and_acquire_lock(self):
        try:
            query = "select * from public.ct_job_lock where checking = true and id = 1"
            self.cur.execute(query)
            results = self.cur.fetchall()
            while len(results) > 0:
                print("lock is there. sleeping for 2 seconds")
                time.sleep(2)
                self.cur.execute(query)
                results = self.cur.fetchall()

            self.acquire_lock(True)
        except Exception as e:
            print(f"Exception occurred while checking lock: {e}")
            print(traceback.format_exc())
            self.close_db_conn()

    def acquire_lock(self, action: bool):
        try:
            update_stmt = """UPDATE public.ct_job_lock SET checking = %s, modified_date = %s where id = 1"""
            data = (action, datetime.datetime.utcnow())
            print(self.cur.mogrify(update_stmt, data))
            self.cur.execute(update_stmt, data)
            self.conn.commit()
        except Exception as e:
            print(traceback.format_exc())
            self.close_db_conn()
            self.acquire_lock(False)

    # see which business was last processed
    def get_last_biz_id_processed(self):
        try:
            query = "select last_biz_id from last_biz_id_processed order by modified_date desc limit 1"
            self.cur.execute(query)
            rows = self.cur.fetchall()
            if len(rows) > 0:
                self.last_biz_id = rows[0][0]
        except Exception as e:
            print(f"Exception occurred while checking lock: {e}")
            print(traceback.format_exc())
            self.close_db_conn()

    def divide_businesses_into_separate_list(self):

        # greater than zero check is more for when we start the business no one has ever processed
        # or in case we ever need to start from scratch
        if self.last_biz_id > 0:
            # we found last biz processed ...divide based on this biz

            # if all docs are processed for last biz id then we should not get it from db
            # so we start from the beginning of list again
            if self.last_biz_id in self.main_biz_list:
                index_of_last_biz = self.main_biz_list.index(self.last_biz_id) + 1
                self.right_list = self.main_biz_list[index_of_last_biz:]
                self.left_list = self.main_biz_list[:index_of_last_biz]
            else:
                self.right_list = self.main_biz_list[0:]
                self.left_list = self.main_biz_list[:0]
        else:
            # there was no last biz processed...time to randomly pick one
            self.right_list = self.main_biz_list[0:]
            self.left_list = self.main_biz_list[:0]

    def rest_call(self, payload):
        url = "http://localhost:8080/ctakes-web-rest/service/analyze"

        querystring = {"pipeline": "Full"}

        headers = {
            'Content-Type': "application/json"
        }

        rest_resp = None

        try:
            rest_resp = requests.request("POST", url, data=json.dumps(payload), headers=headers, params=querystring)
            print(rest_resp.text, rest_resp.status_code)
            return rest_resp.status_code
        except requests.exceptions.RequestException as e:
            logger.info(f"Exception in rest_call: {e}")
            logger.info(traceback.print_exc(file=sys.stdout))
            if rest_resp is not None:
                logger.info(rest_resp.text)
            return 500

    def helper_function_query_call_api(self, biz: int):
        if self.number_of_processes_available > 0 or self.newDocArrivalSignal:
            query = f"select id, business_id, file_id, new_file_name, splitter_status, splitter_user_id, " \
                f"extract_file_name from public.file_state where business_id = {biz} " \
                f"and ctakes_server_status = 'UNASSIGNED' order by last_modified_instant asc limit 2"

            self.cur.execute(query)
            rows = self.cur.fetchall()

            if len(rows) == 0:
                if biz in self.left_list:
                    idx = self.left_list.index(biz)
                    self.left_list.pop(idx)
                elif biz in self.right_list:
                    idx = self.right_list.index(biz)
                    self.right_list.pop(idx)

            payload_list = list()
            for result in rows:
                payload = dict()
                payload['id'] = result[0]
                payload['businessId'] = result[1]
                payload['fileId'] = result[2]
                payload['file_name'] = result[3]
                payload['splitterStatus'] = result[4]
                payload['userId'] = result[5]
                payload['extractFileName'] = result[6]
                payload["bucket"] = "starfizz-staging"
                payload['debug'] = False
                payload_list.append(payload)

            print(payload_list)

            if len(payload_list) > 0:
                status_code: int = self.rest_call(payload_list)
                if status_code == 201:
                    # we have used up one core from available core of the server
                    # notify counter to reduce by 1
                    if self.number_of_processes_available != 0:
                        self.number_of_processes_available -= 1
                elif status_code == 403:
                    self.status_code_403 += 1
                elif status_code == 500:
                    self.status_code_500 += 1

    def update_last_biz_process(self):
        try:
            update_stmt = """UPDATE public.last_biz_id_processed SET last_biz_id = %s, modified_date = %s where id = 1"""
            data = (self.last_biz_id, datetime.datetime.utcnow())
            print(self.cur.mogrify(update_stmt, data))
            self.cur.execute(update_stmt, data)
            self.conn.commit()
        except Exception as e:
            print(traceback.format_exc())
            self.close_db_conn()
            self.acquire_lock(False)

    def loop_through_biz_and_call_api(self):
        print("Right list:", self.right_list, "Left list:", self.left_list)

        while self.number_of_processes_available != 0 or self.newDocArrivalSignal:

            if len(self.right_list) > 0 and len(self.left_list) > 0:
                break

            if len(self.right_list) > 0:
                for biz in self.right_list:
                    self.helper_function_query_call_api(biz)
                    self.last_biz_id = biz

            if len(self.left_list) > 0:
                for biz in self.left_list:
                    self.helper_function_query_call_api(biz)
                    self.last_biz_id = biz

            if self.status_code_403 > 10:
                self.left_list = self.right_list = []

            if self.status_code_500 > 10:
                self.left_list = self.right_list = []

            if len(self.right_list) == 0 and len(self.left_list) == 0:
                self.number_of_processes_available = 0

            if self.number_of_processes_available != 0:
                logger.info("Cores may still be available to process. Sleeping for 2 seconds before retrying")
                time.sleep(2)

            # if we are in this loop because a new doc has arrived then that means we only need to loop once
            # and then exit. For that we need to set newDocArrivalSignal to False...
            if self.newDocArrivalSignal:
                self.newDocArrivalSignal = False

        self.update_last_biz_process()


if __name__ == "__main__":

    e = {"AVAILABLE_CORES": "2", "TOTAL_PROCESSES": "2", "TOTAL_CPU_CORE_COUNT": "4", "LOCAL_HOST_NAME": "848c2f36d5b6",
         "LOCAL_IP_ADDRESS": "172.17.0.2", "TYPE": "onInit"}

    client = boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    while True:
        response = client.receive_message(
            QueueUrl=os.getenv("AWS_SQS_Q_NAME"),
            AttributeNames=[
                'All',
            ],
        )

        if "Messages" in response:
            print(response)
            e = json.loads(response["Messages"][0]["Body"])

            d = JobManager(e)
            d.get_last_biz_id_processed()
            d.get_distinct_biz_ids()
            d.divide_businesses_into_separate_list()
            d.loop_through_biz_and_call_api()

            d.acquire_lock(False)
            print("te")
            response = client.delete_message(
                QueueUrl=os.getenv("AWS_SQS_Q_NAME"),
                ReceiptHandle=response["Messages"][0]["ReceiptHandle"]
            )
        print("Nothing available.Sleeping...")
        time.sleep(20)
