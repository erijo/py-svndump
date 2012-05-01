# Copyright (c) 2012 Erik Johansson <erik@ejohansson.se>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import io

from .record import *

class DumpFileError(Exception):
    def __init__(self, offset, last_line, message):
        Exception.__init__(self)
        self._offset = offset
        self._last_line = last_line
        self._message = message

    def __str__(self):
        return "%s (line: '%s', offset: %d)" % (
            self._message, self._last_line, self._offset)

class DumpFile(object):
    def __init__(self, file, mode, codec):
        object.__init__(self)
        self._buffer = io.open(file, mode=mode, closefd=False)
        self._codec = codec

class DumpFileReader(DumpFile):
    def __init__(self, file, codec='ascii'):
        DumpFile.__init__(self, file, 'rb', codec=codec)
        self._record = None
        self._offset = 0
        self._last_line = ""
        self._blocker = None

    def error(self, message):
        raise DumpFileError(self._offset, self._last_line, message)

    def block(self, blocker):
        self._blocker = blocker

    def unblock(self, blocker):
        assert self._blocker == blocker
        self._blocker = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._record is not None:
            self._record.discard()
            self._record = None

        try:
            while True:
                data = self._buffer.peek(1)
                if len(data) == 0 or not data[0].decode(self._codec).isspace():
                    break
                self._offset += len(self._buffer.read(1))

            self._record = Record.read(self)
        except UnicodeDecodeError as e:
            self.error(str(e))

        if self._record is None:
            if len(self.read(1)) == 0:
                raise StopIteration
            else:
                self.error("premature end")
        return self._record
    next = __next__

    def readline(self, caller=None):
        assert caller is None or caller == self._blocker
        line = self._buffer.readline()
        if len(line) == 0:
            raise EOFError()
        self._offset += len(line)
        self._last_line = line[:-1].decode(self._codec)
        return self._last_line

    def read(self, length, caller=None):
        assert caller is None or caller == self._blocker
        data = self._buffer.read(length)
        self._offset += len(data)
        return data

class DumpFileWriter(DumpFile):
    def __init__(self, file, codec='ascii'):
        DumpFile.__init__(self, file, 'wb', codec=codec)

    def writeline(self, line=""):
        data = "%s\n" % line
        self._buffer.write(data.encode(self._codec))

    def write(self, data):
        if hasattr(data, 'write'):
            data.write(self)
        else:
            self._buffer.write(data)
