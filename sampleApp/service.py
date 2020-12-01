# -*- coding: utf-8 -*-
import http.client
import time

import copy
import traceback

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response
from flask import render_template
from flask import make_response
from flask import current_app
from flask import abort,redirect, url_for

from datetime import timedelta
from functools import update_wrapper
import common
import app_context
from enums.question import QuestionTypes
import logger

app_context = app_context.AppContext()
app = Flask(__name__)


def spam_check(func):
    """
    Decorator function that checks when last request was made and
    if period is greater than given value request will be processed.
    Otherwise request will be treated as a spam.
    """
    # TODO: add logic for blocking teams that made more than X request in last eg. 1m
    def checker(*args_, **kwargs_):
        """
        args_ contains: [team_id, ...]
        """
        is_spam = common.check_if_spam(team_id=args_[0], spam_table=app_context.spam_table,
                                       seconds=app_context.settings["service_config"]["post_delay"])
        if not is_spam:
            return func(*args_, **kwargs_)
        return "Too many requests. Please try again after a few seconds.", 429  # code for 'Too many requests'
    return checker


def team_check(func):
    """
    Decorator function that checks if given team_id is on the list of valid teams.
    """
    def checker(*args_, **kwargs_):
        """
        args_ contains: [team_id, ...]
        """
        if args_[0] is not None and common.is_id_present(id=args_[0], dict_obj=app_context.team_loader.get_key('teams')):
            return func(*args_, **kwargs_)
        return u"Team with id: '{0}' was not found.".format(args_[0]), http.client.UNAUTHORIZED
    return checker


def answer_check(func):
    """
    Decorator function that checks:
    1. if question id is present
    2. if question was already answered by team,
    3. if question type is correct - open/closed
    """
    def checker(*args_, **kwargs_):
        """
        args_ contains: [team_id, question_id, question_type, ...]
        """
        if args_[0] is not None and common.is_id_present(id=args_[1], dict_obj=app_context.question_loader.get_key('questions')):
            if common.check_question_type(question_id=args_[1], question_type=args_[2],
                                          question_dict=app_context.question_loader.get_key('questions')):
                if args_[1] is not None and not common.check_if_was_answered(team_id=args_[0], question_id=args_[1],
                            answered_question_table=app_context.answers_table):  # or app_context.allow_to_change_answer:
                    return func(*args_, **kwargs_)
                return u"Team with id: '{0}' already answered question with id: '{1}'".format(args_[0], args_[1]), http.client.NOT_ACCEPTABLE
        return u"No {0} question with id: '{1}'".format(args_[2], args_[1]), http.client.NOT_ACCEPTABLE
    return checker


def get_all_open_questions_ids():
    open_questions_ids = list()
    questions_dict = app_context.question_loader.get_key('questions')
    for question_key in questions_dict:
        if questions_dict[question_key].get('type', None).lower() == QuestionTypes.OPEN:
            open_questions_ids.append(questions_dict[question_key].get('id', None))
    return open_questions_ids


def get_team_name(team_id):
    team_dict = app_context.team_loader.get_key('teams')
    for team_key in team_dict:
        if team_dict[team_key].get('id', None) == team_id:
            return team_key


def get_answers(already_checked):
    app_context.bugs = app_context.data_manager.get_bugs()

    open_questions_ids = get_all_open_questions_ids()
    answers = app_context.data_manager.get_all_answers()
    for answer in answers:
        if int(answer[0]) in open_questions_ids:
            app_context.bugs.append(answer)

    app_context.already_checked = app_context.data_manager.get_already_checked_answers()

    extended_bugs = list()

    for bug in app_context.bugs:
        if int(bug[0]) in open_questions_ids:
            question_id = (int(bug[0]),)
        else:
            question_id = ('NULL',)
        element = question_id + bug
        extended_bugs.append(element)


    marked_context = list()
    not_marked_context = copy.deepcopy(extended_bugs)

    for bug in extended_bugs:
        for verified in app_context.already_checked:
            if bug[2] in verified:
                new_context_element = bug + (verified[7:12])
                marked_context.append(new_context_element)
                if bug in not_marked_context:
                    not_marked_context.remove(bug)

    if already_checked:
        app_context.answers = marked_context
    else:
        app_context.answers = not_marked_context

    logger.logfile("New results: {0}".format(app_context.results))
    return app_context.answers


def process_results():
    teams_data = app_context.team_loader.get_key('teams')
    if app_context.results is None or app_context.last_results_request is None or \
            time.time() - app_context.last_results_request > app_context.results_generation_delay:
        team_results_dict = app_context.data_manager.get_results(teams_data)
        app_context.results = common.sort_results(team_results_dict)

        app_context.last_results_request = time.time()
        logger.console("New results generated at {0}".format(common.get_date_time()))
        logger.logfile("New results: {0}".format(app_context.results))
    return app_context.results


#@spam_check
@team_check
@answer_check
def process_answer(team_id, question_id, question_type, answer_content):
    team_name = get_team_name(team_id)
    open_question = question_type.lower() == QuestionTypes.OPEN
    db_failure, file_response, creation_time, counter, question_guid = app_context.data_manager.add_answer(team_id, question_id, answer_content, open_question=open_question)
    if db_failure is False:
        if open_question is False:
            # check if answer is correct for closed questions
            is_correct = common.is_question_correct(question_id, answer_content, question_dict=app_context.question_loader.get_key('questions'))
            points = 0
            if is_correct:
                points = common.get_closed_answer_points(question_id, question_dict=app_context.question_loader.get_key('questions'))
            failure, response = app_context.data_manager.insert_answer_result(team_id, question_id, question_guid, points=points)
        return "Answer for question '{0}' for team {1} added.".format(question_id, team_name, counter, creation_time), http.client.CREATED
    else:
        return "Answer was not created for team {0}.".format(team_name), http.client.UNPROCESSABLE_ENTITY


#@spam_check
@team_check
def process_bug(team_id, bug_content):
    team_name = get_team_name(team_id)
    db_failure, file_response, creation_time, counter = app_context.data_manager.add_bug(team_id, bug_content)
    if db_failure is False:
        return "Note created for team {0}.".format(team_name, counter, creation_time), http.client.CREATED
    else:
        return "Note was not created for team {0}.".format(team_name), http.client.UNPROCESSABLE_ENTITY

def _mark_question_answer(team_id, question_guid, question_id, points):
    """
    Marks answer for question.
    :return: bool - True if failure
    :return: response
    """
    was_parsed, value = common.get_float_from_string(points)
    if was_parsed:
        return app_context.data_manager.mark_question_answer(team_id, question_guid, question_id, value)
    else:
        return True, "Could not parse '{0}'".format(points)

def _mark_bug(team_id, bug_guid, bug_id, points):
    was_parsed, value = common.get_float_from_string(points)
    if was_parsed:
        return app_context.data_manager.mark_bug(team_id, bug_guid, bug_id, points)
    else:
        return True, "Could not parse '{0}'".format(points)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_bug')
def send_bug():
    time.sleep(5)
    return render_template('send_bug.html')


@app.route('/send_closed_answer')
def send_closed_answer():
    return render_template('send_closed_answer.html')


@app.route('/send_open_answer')
def send_open_answer():
    return render_template('send_open_answer.html')


@app.route('/rawresults', methods=['GET'])
def get_rawresults():
    return str(process_results()), http.client.OK


@app.route('/results', methods=['GET'])
def get_results():
    try:
        results = process_results()
    except Exception as e:
        results = [("Wystapil problem! Skontaktuj sie z administratorem!", "")]
        logger.console_fatal("Exception message='{0}'. Stack trace='{1}'".format(e, traceback.format_exc()))
    return render_template("results.html", results=results)


@app.route('/answer_verification', methods=['GET'])
def verify_answers():
    if request.args:
        if 'already_checked' in request.args:
            answers = get_answers(already_checked=1)
        elif 'not_checked' in request.args:
            answers = get_answers(already_checked=0)
    else:
        answers = get_answers(already_checked=0)
    return render_template("verify_answers.html", answers=answers)


@app.route('/answer_verification/update_points', methods=['POST'])
def update_points():
    failure, response = app_context.data_manager.mark_bug(request.form['team_id'],
                                                          request.form['question_id'],
                                                          request.form['bug_id'],
                                                          request.form['bug_guid'],
                                                          request.form['base_points'],
                                                          request.form['bonus_for_first'],
                                                          request.form['bonus_for_unique'],
                                                          request.form['other_bonus'],
                                                          request.form['comment'])
    if failure is False:
        print(str(response)), http.client.OK
    else:
        print(str(response)), http.client.UNPROCESSABLE_ENTITY
    if 'answer_verification?already_checked=1' in request.headers.environ['HTTP_REFERER']:
        return redirect(url_for('verify_answers', already_checked=1))
    else:
        return redirect(url_for('verify_answers'))

@app.route('/markbug/<team_id>/<bug_guid>/<bug_id>', methods=['POST'])
def mark_bug(team_id=None, bug_guid=None, bug_id=None):
    logger.console("Request mark bug from {0}, request.data: {1}, {2}, {3}, {4}".format(request.remote_addr, team_id,
                                                                                   bug_guid, bug_id, request.data))
    failure, response = _mark_bug(team_id, bug_guid, bug_id, points=request.data)
    if failure is False:
        return str(response), http.client.OK
    else:
        return str(response), http.client.UNPROCESSABLE_ENTITY


@app.route('/markanswer/<team_id>/<question_guid>/<question_id>', methods=['POST'])
def mark_answer(team_id, question_guid, question_id):
    logger.console("Request mark answer from {0}, request.data: {1}".format(request.remote_addr, request.data))
    failure, response = _mark_question_answer(team_id, question_guid, question_id, points=request.data)
    if failure is False:
        return str(response), http.client.OK
    else:
        return str(response), http.client.UNPROCESSABLE_ENTITY


@app.route('/sendbug/<team_id>', methods=['POST'])
def api_send_bug(team_id=None):
    message, code = process_bug(team_id, request.data)
    page = render_template("message.html", message=message)
    data = {
        "message": message,
        "status": code,
        "page": page
    }
    return jsonify(results=data)
#     return json.dumps({'success':True}), 200, {'ContentType':'application/json'}


@app.route('/sendanswer/<team_id>/<question_id>/<question_type>', methods=['POST'])
def api_send_answer(team_id=None, question_id=None, question_type=None):
    return process_answer(team_id, question_id, question_type, request.data)


@app.route('/postformbug', methods=['POST'])
def form_send_bug():
    try:
        message, status_code = process_bug(request.form['team_id'], request.form['bug_content'])
    except Exception as e:
        message = "Wystapil problem! Skontaktuj sie z administratorem!"
        status_code = http.client.INTERNAL_SERVER_ERROR
        logger.console_fatal("Exception message='{0}'. Stack trace='{1}'".format(e, traceback.format_exc()))
    return render_template("message.html", message=message), status_code


@app.route('/postformanswer/open', methods=['POST'])
def form_send_open_answer():
    try:
        message, status_code = process_answer(request.form['team_id'], request.form['question_id'], "open", request.form['answer'])
    except Exception as e:
        message = "Wystapil problem! Skontaktuj sie z administratorem!"
        logger.console_fatal("Exception message='{0}'. Stack trace='{1}'".format(e, traceback.format_exc()))
    return render_template("message.html", message=message)


@app.route('/postformanswer/closed', methods=['POST'])
def form_send_closed_answer():
    try:
        message, status_code = process_answer(request.form['team_id'], request.form['question_id'], "closed", request.form['answer'])
    except Exception as e:
        message = "Wystapil problem! Skontaktuj sie z administratorem!"
        logger.console_fatal("Exception message='{0}'. Stack trace='{1}'".format(e, traceback.format_exc()))
    return render_template("message.html", message=message)


@app.errorhandler(http.client.NOT_FOUND)
def not_found(error):
    return "Something went wrong! {0}".format(error), http.client.NOT_FOUND


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app_context.settings["service_config"]["port"], debug=True)
