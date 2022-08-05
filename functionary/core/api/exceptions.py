from rest_framework.exceptions import APIException


class BadRequest(APIException):
    """Default error handling exceptions for invalid requests to the system"""

    status_code = 400
    default_detail = "Request is invalid"
    default_code = "bad_request"
