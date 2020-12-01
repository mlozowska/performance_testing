import os

from common import database_connect

primary_db_path = os.path.join(os.path.dirname(__file__), "database/primary.db")
results_db_path = os.path.join(os.path.dirname(__file__), "database/results.db")

def init(primary_db_path, results_db_path):
    primary_cursor, primary_connect = database_connect(primary_db_path)
    results_cursor, results_connect = database_connect(results_db_path)

    create_query = "CREATE TABLE IF NOT EXISTS BUGS (" \
                   "ID INT," \
                   "BUG_GUID TEXT," \
                   "CREATED_DATE_TIME DATETIME," \
                   "TEAM_ID TEXT, BUG_CONTENT TEXT)"

    create_answers_table_query = "CREATE TABLE IF NOT EXISTS ANSWERS (" \
                                 "QUESTION_ID TEXT," \
                                 "QUESTION_GUID TEXT," \
                                 "CREATED_DATE_TIME DATETIME," \
                                 "TEAM_ID TEXT," \
                                 "ANSWER_CONTENT TEXT)"

    primary_cursor.execute(create_query)
    primary_cursor.execute(create_answers_table_query)

    create_query = "CREATE TABLE IF NOT EXISTS RESULTS (" \
                   "ID INT," \
                   "TEAM_ID TEXT," \
                   "QUESTION_GUID TEXT," \
                   "QUESTION_ID TEXT," \
                   "BUG_GUID TEXT," \
                   "BUG_ID TEXT," \
                   "CREATED_DATE_TIME DATETIME," \
                   "BASE_POINTS REAL," \
                   "BONUS_FOR_FIRST REAL,"\
                   "BONUS_FOR_UNIQUE REAL,"\
                   "OTHER_BONUS REAL,"\
                   "COMMENT TEXT," \
                   "ALREADY_CHECKED BOOL INT)"
    results_cursor.execute(create_query)

if __name__ == '__main__':
    init(primary_db_path, results_db_path)
