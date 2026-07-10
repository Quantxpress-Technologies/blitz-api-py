class BlitzSDKException(Exception):
    pass

class AuthenticationError(BlitzSDKException):
    pass

class RequestError(BlitzSDKException):
    def __init__(self, status_code: int, message: str, body: str = ""):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Request failed ({status_code}): {message}")
