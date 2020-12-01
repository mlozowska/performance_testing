import httplib
import unittest
import service


class SqlInjectionTests(unittest.TestCase):

    def setUp(self):
        self.app = service.app.test_client()

    def tearDown(self):
        pass

    def test_sql_injection(self):
        expected_status_code = httplib.UNPROCESSABLE_ENTITY
        team_id = 'test_team'
        bug_content = "content'); SELECT * FROM BUGS; --"
        response = self.app.post("/sendbug/{0}".format(team_id), data=bug_content)
        assert response.status_code == expected_status_code, \
            "Expected status code: {0}, actual: {1}, message: {2}".format(expected_status_code, response.status_code, response.data)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()