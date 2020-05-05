class BaseException(Exception):
    def __str__(self):
        return self.message


class ExtensionError(BaseException):
    def __init__(self, message: str):
        self.message = message


class UnknownChordError(BaseException):
    def __init__(self, message: str):
        self.message = message


class UnableToTransitionError(BaseException):
    def __init__(self, message: str):
        self.message = message
