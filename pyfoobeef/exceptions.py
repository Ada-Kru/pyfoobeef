class ConnectError(Exception):
    """
    Exception for errors relating to connecting to beefweb.

    :param original_exception: The original exception made by the HTTP
        handler.
    """

    def __init__(self, original_exception: Exception):
        self.original_exception = original_exception
        """The original exception made by the HTTP handler."""

    def __str__(self):
        return (
            f"Could not connect to the beefweb server.\n"
            f"Original exception: {self.original_exception}"
        )


class RequestError(Exception):
    """
    Exception for errors relating to making requests to beefweb.

    :param response_code: The HTTP status code returned by the request.
    :param response_data: The parsed data from beefwebs JSON response.
    """

    def __init__(self, response_code: int, response_data: dict):
        self.response_code = response_code
        """The HTTP status code returned by the request."""
        self.response_data = response_data
        """The parsed data from beefwebs JSON response."""

    def __str__(self):
        return (
            f"HTML error code: {self.response_code}. "
            f"Response: {self.response_data}"
        )
