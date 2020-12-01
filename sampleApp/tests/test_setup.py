import os
import unittest

import service
import database_init
import data_manager
import app_context

class TestSetUp(unittest.TestCase):

    def setUp(self):
        primary_db_path = os.path.join(os.path.dirname(__file__), "database\\primary.db")
        results_db_path = os.path.join(os.path.dirname(__file__), "database\\results.db")

        if os.path.isfile(primary_db_path):
            os.remove(primary_db_path)
        if os.path.isfile(results_db_path):
            os.remove(results_db_path)

        service.app_context = app_context.AppContext()
        database_init.init(primary_db_path, results_db_path)
        service.app_context.data_manager = data_manager.DataManager(primary_db_path=primary_db_path,
                                                     result_db_path=results_db_path,
                                                     bug_files_path=service.app_context.settings["db_config"]["bug_files_path"],
                                                     open_questions_files_path=service.app_context.settings["db_config"]["open_questions_files_path"],
                                                     closed_questions_files_path=service.app_context.settings["db_config"]["closed_questions_files_path"])

        self.app = service.app.test_client()

    def tearDown(self):
        service.app_context.data_manager.close()
