import Appy
import time
import CustomAppyErrorParser
import CustomErrorReporter
import TransactionManager
import Transaction

UNACCOUNTED_PURCHASES_VALUE_THRESHOLD = 10.0

import json
import os
import CustomTransactionParser


class ExcludedIdentificatorsLoader(object):
    def __init__(self, file_name):

        self.file_name = file_name
        self._excluded_identificators = None

    def _load_data(self):

        try:
            with open(self.file_name) as data_file:
                json_data = json.load(data_file)
            self._excluded_identificators = json_data['excluded_identificators']
        except IOError:
            self._excluded_identificators = dict()

    def get_excluded_tables(self, force_load=False):

        if force_load or self._excluded_identificators is None or len(self._excluded_identificators) == 0:
            self._load_data()
        return self._excluded_identificators

class ErrorPatternsLoader(object):
    def __init__(self, file_name):

        self.file_name = file_name
        self._error_patterns = None

    def _load_data(self):

        try:
            with open(self.file_name) as data_file:
                json_data = json.load(data_file)
            self._error_patterns = json_data['error_patterns']
        except IOError:
            self._error_patterns = dict()

    def get_error_patterns(self, force_load=False):

        if force_load or self._error_patterns is None or len(self._error_patterns) == 0:
            self._load_data()
        return self._error_patterns


class Customer():
    def __init__(self):

        self.name = None
        self.surname = None
        self.email = None
        self.address = None
        self.telepone = None
        self.customerId = None
        self.is_valid = False
        self.is_rejected = False
        self.is_blocked = False

        self.purchase_list = list()

    def accounted_purchases_value(self):

        return sum([purchase.value for purchase in self.purchase_list if purchase.accounted == True])

    def unaccounted_purchases_value(self):

        return sum([purchase.value for purchase in self.purchase_list if purchase.accounted == False])

    def has_unaccounted_purchases(self):

        return True if len(
            [purchase.value for purchase in self.purchase_list if purchase.accounted == False]) else False

    def get_summary(self):
        summary = "{0} {1} with id: {2} ({3} {4} {5})".format(self.name, self.surname, self.customerId, self.email,
                                                          self.address, self.telepone)
        summary = "Accounted purchases value: {0}".format(self.accounted_purchases_value())
        summary = "Unaccounted purchases value: {0}".format(self.unaccounted_purchases_value())
        return summary


class UserTransaction(Transaction):
    def __init__(self):

        self.user_id = None
        self.user_details = None
        self.user_errors = dict()
        self.error_params = dict()


class RulesEnum():
    def __init__(self):

        self.CRITICAL = 'CRITICAL'
        self.TRIVIAL = 'TRIVIAL'
        self.CUSTOM = 'CUSTOM'
        self.OUTDATED = 'OUTDATED'


class TransactionErrorManager():
    def __init__(self):

        pass

    def parse_transactions_with_id_longer_than_given_length_and_with_unaccounted_sales(self, transaction, length):
        if transaction is not None and len(transaction.id) > length:
            if transaction.error_params is not None:
                if "sale_customer_list" in transaction.error_params:
                    for customer in transaction.error_params["sale_customer_list"]:
                        if customer.has_unaccounted_purchases():
                            if customer.unaccounted_purchases_value() > UNACCOUNTED_PURCHASES_VALUE_THRESHOLD:
                                parameters = CustomTransactionParser.parse_transaction(transaction)

        return parameters


    def poll_for_transaction_with_given_user_id(self, user_id, transaction_id):

        """
        Polls for transaction by user id
        :param: user_id
        :return: transaction
        """
        while True:
            transaction = self.get_transaction_by_user_id(user_id, transaction_id)
            if transaction is not None and transaction.user_id == user_id:
                return transaction
            time.sleep(1)
        return transaction

    def get_transaction_by_user_id(self, transaction_id, user_id):

        """
        Gets transactions by user id
        :param: user_id
        :param: transaction_id
        :return: transaction
        """
        tm = TransactionManager()
        transaction = tm.get_transaction(user_id, transaction_id)
        return transaction

    def send_user_errors(self, transaction, rules):

        """
        Parses errors in transaction according to given rules and sends alerts and warnings.
        Uses CustomErrorReporter to send alerts (for CRITICAL and CUSTOM errors) and warnings for any other.
        :param: transaction
        :param: rules
        """
        customErrorReporter = CustomErrorReporter()
        for error_type in transaction.user_errors:
            x = None
            error_parameters = None
            if error_type.upper() == RulesEnum.CRITICAL:
                x = RulesEnum.CRITICAL
                error_parameters = transaction.error_params
            if error_type.upper() == RulesEnum.TRIVIAL:
                x = RulesEnum.TRIVIAL
            if error_type.upper() == RulesEnum.CUSTOM:
                x = RulesEnum.CUSTOM
                error_parameters = transaction.error_params
            if error_type.upper() == RulesEnum.OUTDATED:
                x = RulesEnum.OUTDATED
            if error_parameters is not None:
                error_parameters["custom_message"] = list()
        for parameter in error_parameters:
            if parameter == "custom_email":
                error_parameters["email"] = error_parameters["custom_email"]
            if parameter == "invalid_deposit":
                error_parameters["custom_message"].append(
                "Invalid deposit value: {0}".format(error_parameters["invalit_deposit"]))
            if parameter == "sales_list":
                sales_sum = sum([sale.value for sale in error_parameters["sales_list"]])
            sales_summary = "\r\n".join([sale.to for sale in error_parameters["sales_list"]])
            error_parameters["custom_message"].append("Invalid sales summary: {0}, {1}".format(sales_sum, sales_summary))
            if parameter == "sale_customer_list":
                customer_summary = "\r\n".join([customer.get_summary() \
                                            for customer in error_parameters["sale_customer_list"] if
                                            (customer.has_unaccounted_purchases() and \
                                             customer.unaccounted_purchases_value() > UNACCOUNTED_PURCHASES_VALUE_THRESHOLD and \
                                             customer.is_valid == True) or customer.is_valid == False or customer.is_rejected == True or customer.is_blocked == True])
            error_parameters["custom_message"].append("Sale customers summary: {0}, {1}".format(sales_sum, sales_summary))

        if x = RulesEnum.CRITICAL:
        if error_parameters is not None and len(error_parameters) > 0:
            customErrorReporter.send_alert()
        else:
            customErrorReporter.send_alert_with_parameters(error_parameters)
        customErrorReporter.set_up()
        customErrorReporter.open_communication_channel()
        if x == RulesEnum.CUSTOM:
            if error_parameters is not None:
                customErrorReporter.send_alert_with_parameters(error_parameters)
            else:
                customErrorReporter.send_alert()
        if x != RulesEnum.CUSTOM or x != RulesEnum.OUTDATED:
            customErrorReporter.send_warning()
        else:
            customErrorReporter.send_warning()
        customErrorReporter.close()
			