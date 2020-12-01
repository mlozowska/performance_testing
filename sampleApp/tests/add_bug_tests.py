import httplib
import os
import unittest
import time
import json

import service
import database_init
import data_manager
import app_context
import test_setup

class Test(test_setup.TestSetUp):

    def setUp(self):
        super(Test, self).setUp()

    def tearDown(self):
        super(Test, self).tearDown()

    def test_add_bug_for_not_existing_team(self):
        team_id = 'not_existing_team_id'
        bug_content = "Test bug content"
        response = self.app.post("/sendbug/{0}".format(team_id), data=bug_content)
        assert response.status_code == httplib.UNAUTHORIZED, \
            "Expected status code: {0}, actual: {1}, message: {2}".format(httplib.UNAUTHORIZED, response.status_code, response.data)

    def test_add_bug_for_existing_team(self):
        team_id = 'test_team'
        bug_content = "Test bug content"
        response = self.app.post("/sendbug/{0}".format(team_id), data=bug_content)
        assert response.status_code == httplib.CREATED, \
            "Expected status code: {0}, actual: {1}, message: {2}".format(httplib.UNAUTHORIZED, response.status_code, response.data)

    def test_spam_detection(self):
        team_id = 'test_team'
        bug_content = "Test bug content"
        service.app_context.settings["service_config"]["post_delay"] = 1

        response = self.app.post("/sendbug/{0}".format(team_id), data=bug_content)
        response = self.app.post("/sendbug/{0}".format(team_id), data=bug_content)
        assert response.status_code == 429, \
            "Expected status code: {0}, actual: {1}, message: {2}".format(httplib.UNAUTHORIZED, response.status_code, response.data)

    def test_spam_detection_after_delay(self):
        team_id = 'test_team'
        bug_content = "Test bug content"
        service.app_context.settings["service_config"]["post_delay"] = 1

        response = self.app.post("/sendbug/{0}".format(team_id), data=bug_content)
        time.sleep(service.app_context.settings["service_config"]["post_delay"])
        response = self.app.post("/sendbug/{0}".format(team_id), data=bug_content)
        assert response.status_code == httplib.CREATED, \
            "Expected status code: {0}, actual: {1}, message: {2}".format(httplib.CREATED, response.status_code, response.data)

    def test_sendanswer(self):
        team_id = 'test_team'
        question_id = '4'
        question_type = 'closed'
        bug_content = "B"
        response = self.app.post("/sendanswer/{0}/{1}/{2}".format(team_id, question_id, question_type), data=bug_content)
        assert response.status_code == httplib.CREATED, \
            "Expected status code: {0}, actual: {1}, message: {2}".format(httplib.CREATED, response.status_code, response.data)

    def test_closed_question_answer(self):
        team_name_1 = "test_team"
        team_id_1 = service.app_context.team_loader.get_key('teams')[team_name_1]['id']
        question_id = service.app_context.question_loader.get_key('questions')[4]['id']
        question_type = service.app_context.question_loader.get_key('questions')[4]['type']
        bug_content = service.app_context.question_loader.get_key('questions')[4]['answer']
        answer_points = service.app_context.question_loader.get_key('questions')[4]['points']

        response = self.app.post("/sendanswer/{0}/{1}/{2}".format(team_id_1, question_id, question_type), data=bug_content)

        assert response.status_code == httplib.CREATED, \
            "Expected status code: {0}, actual: {1}, message: {2}".format(httplib.CREATED, response.status_code, response.data)


    def test_results_for_closed_question_answer(self):
        team_name_1 = "test_team"
        team_id_1 = service.app_context.team_loader.get_key('teams')[team_name_1]['id']
        question_id = service.app_context.question_loader.get_key('questions')[4]['id']
        question_type = service.app_context.question_loader.get_key('questions')[4]['type']
        bug_content = service.app_context.question_loader.get_key('questions')[4]['answer']
        answer_points = service.app_context.question_loader.get_key('questions')[4]['points']
        expected_points_1 = answer_points + answer_points * service.app_context.bonuses.QUICKEST_ANSWER_BONUS

        response = self.app.post("/sendanswer/{0}/{1}/{2}".format(team_id_1, question_id, question_type), data=bug_content)
        response = self.app.get("/rawresults")
        assert response.status_code == httplib.OK, \
            "Expected status code: {0}, actual: {1}, message: {2}".format(httplib.OK, response.status_code, response.data)
        data_list = service.app_context.results
        errors = list()
        for tuple in data_list:
            if tuple[0] == team_name_1:
                if tuple[1] != expected_points_1:
                    errors.append("Expected number of points for {0}: {1}, actual: {2}".format(tuple[0], expected_points_1, tuple[1]))
            else:
                if tuple[1] != 0:
                    errors.append("Expected number of points for {0}: {1}, actual: {2}".format(tuple[0], 0, tuple[1]))
        assert len(errors) == 0, errors

    def test_results_for_quickest_answer(self):
        team_name_1 = "test_team"
        team_name_2 = 'test_team_2'
        team_id_1 = service.app_context.team_loader.get_key('teams')[team_name_1]['id']
        team_id_2 = service.app_context.team_loader.get_key('teams')[team_name_2]['id']
        question_id = service.app_context.question_loader.get_key('questions')[4]['id']
        question_type = service.app_context.question_loader.get_key('questions')[4]['type']
        bug_content = service.app_context.question_loader.get_key('questions')[4]['answer']
        answer_points = service.app_context.question_loader.get_key('questions')[4]['points']
        expected_points_1 = answer_points + answer_points * service.app_context.bonuses.QUICKEST_ANSWER_BONUS
        expected_points_2 = answer_points

        response = self.app.post("/sendanswer/{0}/{1}/{2}".format(team_id_1, question_id, question_type), data=bug_content)
        response = self.app.post("/sendanswer/{0}/{1}/{2}".format(team_id_2, question_id, question_type), data=bug_content)
        response = self.app.get("/rawresults")
        assert response.status_code == httplib.OK, \
            "Expected status code: {0}, actual: {1}, message: {2}".format(httplib.OK, response.status_code, response.data)
        data_list = service.app_context.results
        errors = list()
        for tuple in data_list:
            if tuple[0] == team_name_1:
                if tuple[1] != expected_points_1:
                    errors.append("Expected number of points for {0}: {1}, actual: {2}".format(tuple[0], expected_points_1, tuple[1]))
            elif tuple[0] == team_name_2:
                if tuple[1] != expected_points_2:
                    errors.append("Expected number of points for {0}: {1}, actual: {2}".format(tuple[0], expected_points_2, tuple[1]))
            else:
                if tuple[1] != 0:
                    errors.append("Expected number of points for {0}: {1}, actual: {2}".format(tuple[0], 0, tuple[1]))
        assert len(errors) == 0, errors

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()