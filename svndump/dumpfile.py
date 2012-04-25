import io

from .record import *

class DumpFile(object):
    def __init__(self, file, mode):
        object.__init__(self)
        self._buffer = io.open(file, mode=mode, closefd=False)

class DumpFileReader(DumpFile):
    def __init__(self, file):
        DumpFile.__init__(self, file, 'rb')

    def __iter__(self):
        return self

    def __next__(self):
        record = Record.read(self)
        if record is None:
            raise StopIteration
        return record
    next = __next__

    def readline(self):
        line = self._buffer.readline()
        if len(line) == 0:
            raise EOFError()
        return line[:-1].decode('ASCII')

    def read(self, length):
        return self._buffer.read(length)

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
