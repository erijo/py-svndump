import io

from .record import *

class DumpFileError(Exception):
    def __init__(self, offset, last_line, message):
        Exception.__init__(self)
        self.offset = offset
        self.last_line = last_line
        self.message = message

    def __str__(self):
        return "%s (line: '%s', offset: %d)" % (
            self.message, self.last_line, self.offset)

class DumpFile(object):
    def __init__(self, file, mode):
        object.__init__(self)
        self._buffer = io.open(file, mode=mode, closefd=False)

class DumpFileReader(DumpFile):
    def __init__(self, file):
        DumpFile.__init__(self, file, 'rb')
        self.offset = 0
        self.last_line = ""

    def error(self, message):
        raise DumpFileError(self.offset, self.last_line, message)

    def __iter__(self):
        return self

    def __next__(self):
        record = Record.read(self)
        if record is None:
            if len(self.read(1)) == 0:
                raise StopIteration
            else:
                self.error("premature end")
        return record
    next = __next__

    def readline(self):
        line = self._buffer.readline()
        if len(line) == 0:
            raise EOFError()
        self.offset += len(line)
        self.last_line = line[:-1].decode('ASCII')
        return self.last_line

    def read(self, length):
        data = self._buffer.read(length)
        self.offset += len(data)
        return data

class DumpFileWriter(DumpFile):
    def __init__(self, file):
        DumpFile.__init__(self, file, 'wb')

    def writeline(self, line=""):
        data = "%s\n" % line
        self._buffer.write(data.encode('ASCII'))

    def write(self, data):
        if hasattr(data, 'write'):
            data.write(self)
        else:
            self._buffer.write(data)
