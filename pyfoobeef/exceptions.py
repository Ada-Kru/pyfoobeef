class RequestError(Exception):
    """Exception for errors relating to making requests to beefweb."""

    def __init__(self, response_code, response_data):
        """
        Init.

        :param response_code: The HTTP status code returned by the request.
        :param response_data: The parsed data from beefwebs JSON response.
        """
        self.response_code = response_code
        self.response_data = response_data

    def __str__(self):
        return (
            f"HTML error code: {self.response_code}. "
            f"Response: {self.response_data}"
        )
