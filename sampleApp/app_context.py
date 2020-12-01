import os
import yaml

import common
import data_manager
import logger
import logging

class Bonuses():
    QUICKEST_ANSWER_BONUS = 0


class AppContext():
    def __init__(self):
        script_dir = os.path.dirname(__file__)
        config_path = os.path.join(script_dir, 'config', 'config.yaml')
        if os.path.exists(config_path) is False:
            raise Exception("Missing configuration file:" + config_path)

        stream = open(config_path, 'r')
        self.settings = yaml.load(stream)
        self.allow_to_change_answer = self.settings["service_config"]["allow_to_change_answer"]
        primary_db_path = self.settings["db_config"]["primary_db_path"]
        result_db_path = self.settings["db_config"]["result_db_path"]

        team_list_path = os.path.join(script_dir, self.settings["service_config"]["team_list"])
        self.team_loader = common.YamlConfigFileLoader(team_list_path)
        question_list_path = os.path.join(script_dir, self.settings["service_config"]["question_list"])
        self.question_loader = common.YamlConfigFileLoader(question_list_path)

        self.data_manager = data_manager.DataManager(primary_db_path=primary_db_path,
                                                     result_db_path=result_db_path,
                                                     bug_files_path=self.settings["db_config"]["bug_files_path"],
                                                     open_questions_files_path=self.settings["db_config"]["open_questions_files_path"],
                                                     closed_questions_files_path=self.settings["db_config"]["closed_questions_files_path"])

        self.spam_table = dict()  # the key is team ID, value is datetime
        self.answers_table = self.data_manager.get_answered_qestions()  # the key is team ID, value is list with answered questions IDs

        self.results = None
        self.answers = None
        self.last_results_request = None
        self.results_generation_delay = self.settings["service_config"]["results_generation_delay"]

        self.bonuses = Bonuses()
        self.bonuses.QUICKEST_ANSWER_BONUS = self.settings["service_config"]["quickest_answer_bonus"]


        #  Logger setup:
        log_dir = self.settings['log']['output']

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        if self.settings['log']['split_log']:
            logging_file_name = os.path.join(log_dir, "runner_%s.log" % common.get_date_time())
        else:
            logging_file_name = os.path.join(log_dir, "runner.log")

        logging_format = self.settings['log']['format']
        log_on_console = self.settings['log']['log_on_console']

        if self.settings['log']['level'] == 'INFO':
            log_level = logging.INFO

        if self.settings['log']['level'] == 'DEBUG':
            log_level = logging.DEBUG

        if self.settings['log']['level'] == 'WARNING':
            log_level = logging.WARNING

        logger.basicConfig(logging_file_name, log_level, logging_format, log_on_console)