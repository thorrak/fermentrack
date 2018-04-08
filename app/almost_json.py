
# Slightly rewritten version of wsgiref.util.FileWrapper


class AlmostJsonWrapper:
    """Wrapper to convert file-like objects to iterables"""

    def __init__(self, filelike, blksize=8192, closing_string="\r\n]"):
        self.filelike = filelike
        self.blksize = blksize
        self.sent_close = False
        self.closing_string = closing_string
        if hasattr(filelike,'close'):
            self.close = filelike.close

    def __getitem__(self,key):
        data = self.filelike.read(self.blksize)
        if data:
            return data
        elif not self.sent_close:
            self.sent_close = True
            return self.closing_string
        raise IndexError

    def __iter__(self):
        return self

    def __next__(self):
        data = self.filelike.read(self.blksize)
        if data:
            return data
        elif not self.sent_close:
            self.sent_close = True
            return self.closing_string
        raise StopIteration

    # Not sure if this is actually needed, including just in case
    def next(self):
        return self.__next__()