# -*- coding: utf-8 -*-
import os
import uuid
from sqlite3 import OperationalError

import logger
import common


class DataManager():
    def __init__(self, primary_db_path, result_db_path, bug_files_path, open_questions_files_path,
                 closed_questions_files_path):
        self._primary_cursor = None
        self._primary_connection = None

        self._result_cursor = None
        self._result_connection = None

        self._db_table = "BUGS"
        self._db_answer_table = "ANSWERS"
        self._db_results_table = "RESULTS"

        self._bugs_counter = 0

        self._bug_files_path = bug_files_path
        self._closed_questions_files_path = closed_questions_files_path
        self._open_questions_files_path = open_questions_files_path
        self._primary_cursor, self._primary_connection = self._init_cursor(primary_db_path)
        self._result_cursor, self._result_connection = self._init_cursor(result_db_path)

    def close(self):
        """
        Close all cursors and connections
        """
        self._close_connection(self._primary_cursor, self._primary_connection)
        self._close_connection(self._result_cursor, self._result_connection)

    def _close_connection(self, cursor, connection):
        try:
            cursor.close()
            connection.close()
        except Exception as e:
            logger.console_fatal('Error occurred while closing connection to database. Reason: {0}'.format(str(e)))

    def _init_cursor(self, db_path):
        db_path = os.path.join(os.path.dirname(__file__), db_path)
        cursor, connection = common.database_connect(db_path)
        if cursor is None or connection is None:
            raise Exception("No connection to database at '{0}'!".format(db_path))
        connection.text_factory = str
        return cursor, connection

    def _execute_query_on_cursor(self, cursor, connection, query, params):
        response = None
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            connection.commit()
            response = cursor.fetchall()
        except OperationalError as ex:
            response = ex
        return response

    def _execute_query(self, cursor, connection, query, params):
        failure = False
        response = None
        try:
            response = self._execute_query_on_cursor(cursor=cursor, connection=connection, query=query, params=params)
        except Exception as ex:
            logger.console_fatal(ex)
            failure = True
        logger.debug("query: {0}, response: {1}".format(query, response))
        return failure, response

    def _execute_databank_query(self, query, params=None):
        """
        Method executes query on multiple or single database
        :param params
        :return: response from database
        """
        primary_failure, primary_response = self._execute_query(cursor=self._primary_cursor, connection=self._primary_connection, query=query, params=params)
        return primary_failure, primary_response

    def _execute_result_query(self, query, params=None):
        """
        Method executes query on multiple or single database
        :param query
        :return: bool (failure)
        :return: response from database
        """
        return self._execute_query(cursor=self._result_cursor, connection=self._result_connection, query=query, params=params)

    def get_answered_qestions(self):
        """
        Returns answered qestions for each team. If number of answers differs in both DB logs error and returns larger list.
        :return: bool - True if number of answers is equal for both tables
        :return: answers_table
        """
        primary_answers_table = self.get_answered_qestions_per_team()
        return primary_answers_table

    def get_team_ids_from_answer_tabe(self):
        teams_query = 'SELECT DISTINCT TEAM_ID FROM {0}'.format(self._db_answer_table)
        failure, primary_response = self._execute_databank_query(teams_query)
        primary_team_list = [team_id[0] for team_id in primary_response]
        return primary_team_list

    def get_answered_qestions_per_team(self):
        """
        Returns list of id of answered questions per team.
        :return: dictionary of primary table - {team_1: [1, 2, ...], team_2: [3, 7, ...], ...}
        """
        query = "SELECT DISTINCT QUESTION_ID FROM {0} WHERE TEAM_ID = ?".format(self._db_answer_table)
        primary_team_list = self.get_team_ids_from_answer_tabe()
        primary_answers_table = dict()
        for team_id in primary_team_list:
            params = (team_id,)
            failure, primary_response = self._execute_databank_query(query, params=params)
            primary_question_list = [question_id[0] for question_id in primary_response]
            primary_answers_table[team_id] = primary_question_list

        return primary_answers_table

    def get_number_of_bugs_in_databases(self):
        """
        Returns number of records in tables
        :return: number_of_bugs_in_primary_db
        """
        query = "SELECT COUNT(*) FROM {0}" .format(self._db_table)
        failure, primary_response = self._execute_databank_query(query)
        number_of_bugs_in_primary_db = -1
        if primary_response is not None:
            number_of_bugs_in_primary_db = primary_response[0][0]
        return number_of_bugs_in_primary_db

    def get_number_of_bugs(self):
        """
        Returns number of records in tables. If number of bugs differs in both DB logs error and returns larger number.
        :return: bool - True if number of bugs is equal for both tables
        :return: number_of_bugs
        """
        number_of_bugs = self.get_number_of_bugs_in_databases()
        return number_of_bugs

    def _update_counter(self):
        if self._bugs_counter == 0:  # first bug added after server restart
            self._bugs_counter = self.get_number_of_bugs()
        self._bugs_counter += 1

    def get_results(self, teams):
        team_results_dict = dict()
        for team in teams:
            team_results_dict[team] = 0.0
        points_query = "SELECT team_id, sum(BASE_POINTS), sum(BONUS_FOR_FIRST), sum(BONUS_FOR_UNIQUE), sum(OTHER_BONUS)" \
                       "FROM RESULTS group by TEAM_ID"
        query = points_query.format(self._db_results_table)
        failure, response = self._execute_result_query(query)
        for row in response:
            team_name = [team_name for team_name in teams if teams[team_name]['id'] == row[0]]
            if len(team_name) == 1:
                team_results_dict[team_name[0]] = sum(row[1:])

        return team_results_dict

    def get_all_answers(self):
        query = "SELECT * FROM ANSWERS"
        failure, primary_response = self._execute_databank_query(query)
        return primary_response

    def get_bugs(self):
        # answers = list()
        query = "SELECT * FROM BUGS"
        failure, primary_response = self._execute_databank_query(query)
        return primary_response

    def get_already_checked_answers(self):
        query = "SELECT * FROM RESULTS WHERE ALREADY_CHECKED > 0"
        failure, primary_response = self._execute_result_query(query)
        return primary_response

    def insert_answer_result(self, team_id, question_id, question_guid, points=0):
        """
        Adds answer to DB or/and file.
        :param: team_id
        :param: question_id
        :param: question_guid
        :param: answer_content
        :param: points=0
        :return: failure, response
        """
        creation_time = common.get_date_time()
        bug_id = 'NULL'
        bug_guid = 'NULL'
        comment = 'NULL'
        bonus_for_first = bonus_for_unique = other_bonus = 0
        return self._insert_answer_result_to_db(team_id, bug_id, bug_guid, question_id, question_guid, creation_time, \
                    base_points=points, bonus_for_first=bonus_for_first, bonus_for_unique=bonus_for_unique, \
                    other_bonus=other_bonus, comment=comment)

    def mark_bug(self, team_id, question_id, bug_id, bug_guid, base_points,
                 bonus_for_first, bonus_for_unique, other_bonus, comment):
        """
        Adds or updates answer to DB if already marked .
        :param: team_id
        :param: bug_id
        :param: bug_guid
        :param: *_points, bonus_* - different types of points
        :param: comment
        :return: failure, primary_response
        """
        creation_time = common.get_date_time()
        question_guid = 'NULL'
        if question_id == bug_id:
            bug_id = 'NULL'

        if self.check_if_answer_in_results(team_id, bug_guid):
            return self._update_answer_result_to_db(team_id, bug_guid,base_points, bonus_for_first,
                                                    bonus_for_unique, other_bonus,comment)
        else:
            return self._insert_answer_result_to_db(team_id, bug_id, bug_guid, question_id, question_guid, creation_time, base_points, \
                                 bonus_for_first, bonus_for_unique, other_bonus,comment)

    def add_answer(self, team_id, question_id, answer_content, add_to_db=True, add_to_file=True, open_question=True):
        """
        Adds answer to DB or/and file.
        :param: team_id
        :param: question_id
        :param: answer_content
        :param: add_to_db=True
        :param: add_to_file=True
        :return: db_response
        :return: file_response
        :return: creation_time
        :return: self._bugs_counter
        :return: question_guid
        """
        question_guid = uuid.uuid4()
        creation_time = common.get_date_time()

        self._update_counter()
        if add_to_file == True:
            if open_question is True:
                file_path = self._open_questions_files_path
            else:
                file_path = self._closed_questions_files_path
            file_response = self._insert_answer_to_file(team_id, question_id, answer_content, question_guid, creation_time, file_path=file_path)
        # TODO: delete old answer if change in answers is allowed
        if add_to_db == True:
            db_failure, primary_response = self._insert_answer_to_db(team_id, question_id, answer_content, question_guid, creation_time)
        logger.console(u"Answer added. Responses: db_response: {0}. file_response: {1}, creation_time: {2}, {3}".format(primary_response, \
                                                                    file_response, creation_time, self._bugs_counter))
        return db_failure, file_response, creation_time, self._bugs_counter, question_guid

    def add_bug(self, team_id, bug_content, add_to_db=True, add_to_file=True):
        """
        Adds bug to DB or/and file.
        :param: team_id
        :param: bug_content
        :param: add_to_db=True
        :param: add_to_file=True
        :return: db_response
        :return: file_response
        :return: creation_time
        :return: self._bugs_counter
        """
        bug_guid = str(uuid.uuid4())
        creation_time = common.get_date_time()

        self._update_counter()

        if add_to_file == True:
            file_response = self._insert_bug_to_file(team_id, self._bugs_counter, bug_content, bug_guid, creation_time)
        if add_to_db == True:
            db_failure, primary_response = self._insert_bug_to_db(team_id, bug_content, bug_guid, creation_time)
        logger.console(u"Bug added. Responses: db_response: {0}. file_response: {1}, creation_time: {2}, {3}".format(primary_response, \
                                                                    file_response, creation_time, self._bugs_counter))
        return db_failure, file_response, creation_time, self._bugs_counter

    def _insert_bug_to_db(self, team_id, bug_content, bug_guid, creation_time):
        query = "INSERT INTO {0} (ID, BUG_GUID, CREATED_DATE_TIME, TEAM_ID, BUG_CONTENT) \
                VALUES(?, ?, ?, ?, ?)".format(self._db_table)
        params = (
            self._bugs_counter,
            bug_guid,
            str(creation_time),
            str(team_id),
            str(bug_content.encode('utf-8')),)
        failure, primary_response = self._execute_databank_query(query, params=params)
        return failure, primary_response

    def _insert_answer_to_db(self, team_id, question_id, answer_content, question_guid, creation_time):
        query = "INSERT INTO {0} (QUESTION_ID, QUESTION_GUID, CREATED_DATE_TIME, TEAM_ID, ANSWER_CONTENT) \
                 VALUES(?, ?, ?, ?, ?)".format(self._db_answer_table)
        params = (
            str(question_id),
            str(question_guid),
            str(creation_time),
            str(team_id),
            str(answer_content.encode('utf-8')),)
        failure, primary_response = self._execute_databank_query(query, params=params)
        return failure, primary_response

    def _update_answer_result_to_db(self, team_id, bug_guid,
                                    base_points, bonus_for_first, bonus_for_unique, other_bonus,comment):
        query = "UPDATE {0} SET " \
                "BASE_POINTS = ?," \
                "BONUS_FOR_FIRST = ?, " \
                "BONUS_FOR_UNIQUE = ?, " \
                "OTHER_BONUS = ?, " \
                "COMMENT = ?, " \
                "ALREADY_CHECKED = (ALREADY_CHECKED + 1) "\
                "WHERE (TEAM_ID =? AND BUG_GUID = ?)".format(self._db_results_table)
        params = (
                str(base_points),
                str(bonus_for_first),
                str(bonus_for_unique),
                str(other_bonus),
                str(comment.encode('utf-8')),
                str(team_id),
                str(bug_guid)
                ,)
        failure, response = self._execute_result_query(query, params=params)
        return failure, response

    def _insert_answer_result_to_db(self, team_id, bug_id, bug_guid, question_id, question_guid, \
                                    creation_time, base_points, bonus_for_first, bonus_for_unique, other_bonus, comment):

        if base_points is None:
            base_points = 0
        if bonus_for_first is None:
            bonus_for_first = 0
        if bonus_for_unique is None:
            bonus_for_unique = 0
        if other_bonus is None:
            other_bonus = 0

        query = "INSERT INTO {0} (ID," \
                "TEAM_ID," \
                "QUESTION_GUID," \
                "QUESTION_ID," \
                "BUG_GUID," \
                "BUG_ID," \
                "CREATED_DATE_TIME," \
                "BASE_POINTS," \
                "BONUS_FOR_FIRST," \
                "BONUS_FOR_UNIQUE," \
                "OTHER_BONUS," \
                "COMMENT," \
                "ALREADY_CHECKED)"\
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(self._db_results_table)
        params = (
                self._bugs_counter,
                str(team_id),
                str(question_guid),
                str(question_id),
                str(bug_guid),
                str(bug_id),
                str(creation_time),
                str(base_points),
                str(bonus_for_first),
                str(bonus_for_unique),
                str(other_bonus),
                str(comment.encode('utf-8')),
                "1"
                ,)
        failure, response = self._execute_result_query(query, params=params)
        return failure, response

    def _insert_bug_to_file(self, team_id, bug_id, bug_content, bug_guid, creation_time):
        try:
            file_name = os.path.join(self._bug_files_path, '{0}_{1}_{2}_{3}.txt'.format(self._bugs_counter, \
                                                                        str(creation_time.replace(":", "_")), team_id, bug_guid))
            file_handler = open(file_name, "wb")
            logger.console(u"Writing to file: '{0}' content:'{1}'".format(file_name, bug_content))
            file_handler.write(self._format_bug_file_content(team_id, bug_id, bug_content, bug_guid, creation_time).encode('utf-8'))
            file_handler.close()
            return True, None
        except IOError as exc:
            return False, exc

    def _insert_answer_to_file(self, team_id, question_id, answer_content, question_guid, creation_time, file_path):
        try:
            file_name = os.path.join(file_path, '{0}_{1}_{2}_{3}.txt'.format(team_id, question_id, question_guid, \
                                                                           str(creation_time.replace(":", "_"))))
            file_handler = open(file_name, "wb")
            logger.console(u"Writing to file: '{0}', question id: '{1}', content: '{2}'".format(file_name, question_id, answer_content))
            file_handler.write(self._format_question_answer_file_content(team_id, question_id, answer_content, question_guid, creation_time).encode('utf-8'))
            file_handler.close()
            return True, None
        except IOError as exc:
            return False, exc

    def _format_bug_file_content(self, team_id, bug_id, bug_content, bug_guid, creation_time):
        team_id_part = "team id: {0}".format(team_id)
        bug_id_part = "bug id: {0}".format(bug_id)
        bug_guid_part = "bug guid: {0}".format(bug_guid)
        creation_time_part = "bug creation time: {0}".format(creation_time)
        content_part = u"Content: \r\n{0}".format(bug_content)
        return "\r\n".join([team_id_part, bug_id_part, bug_guid_part, creation_time_part, content_part])

    def _format_question_answer_file_content(self, team_id, question_id, answer_content, question_guid, creation_time):
        team_id_part = "team id: {0}".format(team_id)
        bug_id_part = "question id: {0}".format(question_id)
        bug_guid_part = "question guid: {0}".format(question_guid)
        creation_time_part = "answer creation time: {0}".format(creation_time)
        content_part = u"Content: \r\n{0}".format(answer_content)
        return "\r\n".join([team_id_part, bug_id_part, bug_guid_part, creation_time_part, content_part])

    def check_if_answer_in_results(self, team_id, question_guid, question_id=''):
        query = "SELECT * FROM {0} \
                 WHERE TEAM_ID = ? AND ((QUESTION_GUID = ? AND QUESTION_ID = ?)" \
                "OR (BUG_GUID = ?))".format( self._db_results_table)
        params = (
            team_id, str(question_guid), question_id, str(question_guid))
        failure, response = self._execute_result_query(query, params)
        return len(response) > 0

    def check_if_answer_exists(self, team_id, question_guid, question_id):
        query = "SELECT * FROM {0} \
                 WHERE TEAM_ID = ? AND QUESTION_GUID = ? AND QUESTION_ID = ?".format(self._db_answer_table)
        params = (
            team_id, str(question_guid), question_id,)
        failure, primary_response = self._execute_databank_query(query, params)
        return len(primary_response) > 0

    def mark_question_answer(self, team_id, question_guid, question_id, points):
        if self.check_if_answer_exists(team_id, question_guid, question_id):
            if self.check_if_answer_in_results(team_id, question_guid, question_id) is False:
                return self.insert_answer_result(team_id, question_id, question_guid, points=points)
            return True, "Answer already marked"
        return True, "Answer not found"
