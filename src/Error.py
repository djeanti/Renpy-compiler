import inspect

class DetailedError(Exception):
    """Class defining our custom raised error for this project (Used mostly by the parser methods)"""
    def __init__(self, message):
        # Get current frame info
        frame = inspect.currentframe().f_back
        self.function = frame.f_code.co_name
        self.line = frame.f_lineno
        self.class_name = frame.f_locals.get('self', None).__class__.__name__ if 'self' in frame.f_locals else None
        super().__init__(f"{message} | function: {self.function}, line: {self.line}, class: {self.class_name}")
