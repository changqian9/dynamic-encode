from log import logger


# Error class, non re-entrant
class Error(object):
    def __init__(self, message, code=-1):
        self._message = message
        self._code = code

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message

    def get(self):
        return self._code

    def set(self, message, overwrite=False):
        if overwrite:
            logger.info("overwrite error message from {} to {}".format(self._message, message))
            self._message = message
        else:
            # Each new line is a new error message
            self._message += "\n" + message

    def __str__(self):
        return self._message

    def __repr__(self):
        return self._message


# Global Error object
_err = None


# Set new error
def set_error(message, code=-1):
    global _err
    if not _err:
        _err = Error(message, code)
    else:
        _err.set(message)


# Get error message
def get_error():
    global _err
    if not _err:
        return ""
    else:
        return _err.message
