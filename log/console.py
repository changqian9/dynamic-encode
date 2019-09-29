import sys
import os


# Console Class
class Console(object):
    def __init__(self):
        self._quite = False
        self._stdout = sys.stdout
        self._file = None
        self._null = open(os.devnull, "w")
        sys.stdout = self

    def tee(self, name, mode='a'):
        if not self._file:
            try:
                name = os.path.abspath(name)
                f = open(name, mode=mode)
                self._file = f
                return True
            except Exception as e:
                pass
            return False

    def quite(self, val=True):
        self._quite = val

    @property
    def is_quite(self):
        return self._quite

    def __del__(self):
        if sys:
            # sys might not exists at the the time of program exit
            sys.stdout = self._stdout
        if self._file:
            self._file.close()
        self._null.close()

    def write(self, data):
        if self._file:
            self._file.write(data)
        if not self._quite:
            self._stdout.write(data)

    def flush(self):
        if self._file:
            self._file.flush()

    def seek(self, *args, **kwargs):
        if self._file:
            return self._file.seek(*args, **kwargs)

    def tell(self):
        if self._file:
            return self._file.tell()
        return 0

    def fileno(self):
        if self._file:
            return self._file.fileno()
        if self._quite:
            return self._null.fileno()
        return self._stdout.fileno()


console = Console()

