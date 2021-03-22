import psycopg2
from psycopg2.extras import execute_values
import datetime

try:
    conn = psycopg2.connect(
        "dbname='postgres' user='starfizzpg' host='starfizzpg.cxx1bkrproxz.us-west-1.rds.amazonaws.com' password='starfizzpg'")
except:
    print("I am unable to connect to the database")

# print(conn.get_dsn_parameters(), "\n")
# cur = conn.cursor()
# print(cur)
# cur.execute("SELECT * from public.user;")
#
# record = cur.fetchall()
# print("You are connected to - ", record,"\n")


cur = conn.cursor()

l = [(3, 45, "Name0.pdf", datetime.datetime.utcnow(), datetime.datetime.utcnow(), 'fail' if True else 'completed', 16, str({'a': 'b', 'c': 'd'}), datetime.datetime.utcnow()),
     (3, 45, "Name1.pdf", datetime.datetime.utcnow(), datetime.datetime.utcnow(), 'fail' if False else 'completed', 16,
      str({'a': 'b', 'c': 'd'}), datetime.datetime.utcnow()),]

execute_values(cur, "INSERT INTO file_state (business_id, file_id, new_file_name, "
                    "splitter_start_instant, splitter_completed_instant, splitter_status, splitter_user_id,"
                    "splitter_s3_upload_resp, last_modified_instant) VALUES %s RETURNING id, business_id, file_id, new_file_name, splitter_status", l)

conn.commit()

results = cur.fetchall()

s = str({"a": "b", "c": "d"}).replace("'",'"')

for result in results:
    sql = f"UPDATE file_state SET splitter_to_extract_text_hand_off_resp = '{s}'," \
        f" last_modified_instant = '{str(datetime.datetime.utcnow())}' WHERE id = {result[0]} "

    cur.execute(sql)

    conn.commit()

conn.close()

