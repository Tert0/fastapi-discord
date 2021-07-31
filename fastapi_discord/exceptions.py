class Unauthorized(Exception):
    """A Exception raised when user is not authorized."""


class InvalidRequest(Exception):
    """A Exception raised when a Request is not Valid"""


class RateLimited(Exception):
    """A Exception raised when a Request is not Valid"""

    def __init__(self, json, headers):
        self.json = json
        self.headers = headers
        self.message = json["message"]
        self.retry_after = json["retry_after"]
        super().__init__(self.message)


class ScopeMissing(Exception):
    scope: str

    def __init__(self, scope: str):
        self.scope = scope
        super().__init__(self.scope)
