
from wsgiref.util import FileWrapper


class AlmostJsonWrapper(FileWrapper):
    """Wrapper to convert file-like objects to iterables, while appending a string after the file is read"""

    def __init__(self, filelike, blksize=8192, closing_string="\r\n]"):
        super(AlmostJsonWrapper, self).__init__(filelike, blksize=8192)
        self.sent_close = False
        self.closing_string = closing_string

    def __getitem__(self,key):
        import warnings
        warnings.warn(
            "FileWrapper's __getitem__ method ignores 'key' parameter. "
            "Use iterator protocol instead.",
            DeprecationWarning,
            stacklevel=2
        )
        data = self.filelike.read(self.blksize)
        if data:
            return data
        elif not self.sent_close:
            self.sent_close = True
            return self.closing_string
        raise IndexError

    # def __iter__(self):
    #     return self

    def __next__(self):
        data = self.filelike.read(self.blksize)
        if data:
            return data
        elif not self.sent_close:
            self.sent_close = True
            return self.closing_string
        raise StopIteration

    # # Not sure if this is actually needed, including just in case
    # def next(self):
    #     return self.__next__()