# -*- coding: utf-8 -*-
import sqlite3
import time
import yaml
import os
import operator


def get_float_from_string(str_to_parse):
    value = 0
    was_parsed = False
    try:
        value = float(str_to_parse)
        was_parsed = True
    except ValueError:
        pass
    return was_parsed, value


def database_connect(db_path):
    """
    Connecting to database and returns cursor
    :param db_path: path to location with database
    :return: cursor and connection reference
    """
    cursor = None
    connection = None
    try:
        connection = sqlite3.connect(db_path, check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute('SELECT SQLITE_VERSION()')
        data = cursor.fetchone()
        print("SQLite version: %s" % data)
    except sqlite3.Error as e:
        print ("Error %s:" % e.args[0])
    return cursor, connection


def get_date_time():
    """
    Returns current Date Time with zone information.
    """
    return time.strftime('%H:%M:%S', time.localtime())


def check_question_type(question_id, question_type, question_dict):
    question = question_dict.get(int(question_id), None)
    if question is not None and str(question.get("type", None)).lower() == str(question_type).lower():
        return True
    return False


def is_question_correct(question_id, answer, question_dict):
    """
    Checks if question is correct
    :param: question_id
    :param: answer
    :param: question_dict
    :return: bool
    """
    question = question_dict.get(int(question_id), None)
    answer_list = answer.strip().lower().split(' ')
    if question is not None:
        correct_answer_list = question['answer'].lower().split(' ')
        if len(correct_answer_list) != len(answer_list):
            return False
        for correct_answer in correct_answer_list:
            if (correct_answer.strip()) not in (answer_list):
                return False
        return True
    return False


def sort_results(team_results_dict):
    """
    Sorts results by points.
    :param: team_results_dict - where key is a name of a team and value is number of points
    :return: sorted list of tuples, where [0] is team name, and [1] is points
    """
    team_results_dict = sorted(team_results_dict.items(), key=operator.itemgetter(1), reverse=True)
    return team_results_dict


def get_closed_answer_points(question_id, question_dict):
    question = question_dict.get(int(question_id), None)
    if question is not None:
        return question['points']
    return 0


def is_id_present(id, dict_obj, id_key='id'):
    for key_ in dict_obj:
        if id == str(dict_obj[key_].get(id_key, None)):
            return True
    return False


def check_if_spam(team_id, spam_table, seconds=5):
    if team_id not in spam_table:
        spam_table[team_id] = time.time()
        return False
    else:
        if time.time() - spam_table[team_id] > seconds:
            spam_table[team_id] = time.time()
            return False
    return True


def check_if_was_answered(team_id, question_id, answered_question_table):
    if team_id not in answered_question_table:
        answered_question_table[team_id] = list()
    if question_id not in answered_question_table[team_id]:
        answered_question_table[team_id].append(question_id)
        return False
    return True


class YamlConfigFileLoader(object):
    def __init__(self, file_name, check_modification_time=True):
        self.file_name = file_name
        self._json_data = None
        self._modification_time = None
        self._check_modification_time = check_modification_time

    def _load_data(self):
        try:
            with open(self.file_name) as data_file:
                self._json_data = yaml.load(data_file)
            self._modification_time = self._get_last_modification_date()
        except IOError as ex:
            print (ex)
            self._json_data = dict()

    def _get_last_modification_date(self):
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(self.file_name)
        return mtime

    def get_key(self, key, force_load=False):
        if force_load or self._json_data is None or len(self._json_data) == 0:
            self._load_data()
        if self._check_modification_time:
            if self._modification_time < self._get_last_modification_date():
                self._load_data()
        if key in self._json_data.keys():
            return self._json_data[key]
        else:
            return None
