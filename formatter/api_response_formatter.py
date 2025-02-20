from flask import jsonify


class ApiResponseFormatter:
    def __init__(self):
        self.data = []
        self.message = "success"
        self.errors = []
        self.status = 200
        self.additional_data = {}
        self.include_data = True
        self.include_additional_data = True

    def with_data(self, data):
        self.data = data
        return self

    def with_message(self, message):
        self.message = message
        return self

    def with_errors(self, errors):
        self.errors = errors
        return self

    def with_status(self, status):
        self.status = status
        return self

    def with_additional_data(self, additional_data):
        self.additional_data = additional_data
        return self

    def without_data(self):
        self.include_data = False
        self.include_additional_data = False
        return self

    def without_additional_data(self):
        self.include_additional_data = False
        return self

    def with_exception(self, exception):
        self.errors = str(exception)
        self.status = 500
        return self

    def response(self):
        response = {}
        if self.include_data:
            response["data"] = self.data
        response["message"] = self.message
        response["errors"] = self.errors
        response["status"] = self.status
        if self.include_additional_data:
            response["additional_data"] = self.additional_data
        self._reset()
        return jsonify(response), response["status"]

    def _reset(self):
        self.data = []
        self.message = "success"
        self.errors = []
        self.status = 200
        self.additional_data = {}
        self.include_data = True
        self.include_additional_data = True
