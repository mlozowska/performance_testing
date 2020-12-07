from locust import HttpUser, User, task, between, constant, SequentialTaskSet, TaskSet
import time
from datetime import datetime


class TesterActivity(SequentialTaskSet):
    wait_time = constant(1)

    @task
    def home_page(self):
        with self.client.get("/", catch_response=True) as home_page_response:
            if "What you want?" in home_page_response.text:
                home_page_response.success()
            else:
                home_page_response.failure("Content was wrong")

    @task
    def send_bug(self):
        self.client.get("/send_bug")
        response = self.client.post("/postformbug", data={"team_id": "AAA", "bug_content": "jakis blad"})
        assert response.status_code == 201


    @task
    def send_open_answer(self):
        self.client.get("/send_open_answer")
        response = self.client.post("/postformanswer/open",  data={"team_id": "AAA",
                                                                   "question_id": "45",
                                                                   "answer": "abc"})
        assert response.status_code == 200

class TestUserScenario(HttpUser):
    tasks = [TesterActivity]