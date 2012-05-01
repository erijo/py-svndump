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

class Header(object):
    def __init__(self, key, value):
        object.__init__(self)
        self.key = key
        self.value = value

    def write(self, stream):
        stream.writeline("%s: %s" % (self.key, self.value))

    @staticmethod
    def read(stream):
        line = stream.readline()
        if len(line) == 0:
            return None
        header = line.split(': ', 1)
        if len(header) != 2:
            stream.error("invalid header line")
        return Header(header[0], header[1])

class HeaderSection(object):
    def __init__(self, headers):
        object.__init__(self)
        self.headers = headers

    def write(self, stream):
        for header in self.headers:
            header.write(stream)
        stream.writeline()

    @staticmethod
    def read(stream):
        headers = []
        try:
            while True:
                header = Header.read(stream)
                if header is None:
                    break
                headers.append(header)
        except EOFError:
            if len(headers) != 0:
                raise
        if len(headers) == 0:
            return None
        return HeaderSection(headers)

    def __iter__(self):
        return self.headers.__iter__()

    def __getitem__(self, key):
        for header in self.headers:
            if header.key == key:
                return header.value
        try:
            return self.headers[key]
        except TypeError:
            pass
        raise KeyError(key)

    def __setitem__(self, key, value):
        for header in self.headers:
            if header.key == key:
                header.value = value
                return
        raise KeyError(key)

    def __delitem__(self, key):
        for header in self.headers:
            if header.key == key:
                self.headers.remove(header)
                return
        raise KeyError(key)

    def __contains__(self, key):
        for header in self.headers:
            if header.key == key:
                return True
        return False


class PropertySection(dict):
    PROPS_END = "PROPS-END"

    def __init__(self, *args, **kwargs):
        super(PropertySection, self).__init__(*args, **kwargs)

    def dump_length(self):
        length = len(self.PROPS_END) + 1
        for key, value in self.items():
            length += len("X %d\n" % len(key)) + len(key) + 1
            if value is not None:
                length += len("V %d\n" % len(value)) + len(value) + 1
        return length

    def write(self, stream):
        for key, value in self.items():
            if value is None:
                stream.writeline("D %d" % len(key))
            else:
                stream.writeline("K %d" % len(key))
            stream.write(key)
            stream.writeline()

            if value is not None:
                stream.writeline("V %d" % len(value))
                stream.write(value)
                stream.writeline()
        stream.writeline("%s" % self.PROPS_END)

    @staticmethod
    def read(stream):
        def read_segment(stream, line):
            length = int(line[2:])
            segment = stream.read(length)
            if len(segment) != length:
                stream.error("incorrect property length '%s'" % length)
            stream.readline()
            return segment

        section = PropertySection()

        while True:
            line = stream.readline()
            if line == PropertySection.PROPS_END:
                return section

            if line[0] != 'K' and line[0] != 'D':
                stream.error("invalid property key line")
            key = read_segment(stream, line)

            value = None
            if line[0] == 'K':
                line = stream.readline()
                if line[0] != 'V':
                    stream.error("invalid property value line")
                value = read_segment(stream, line)

            section[key] = value


class Content(object):
    CHUNK_SIZE = 2048

    def __init__(self, stream, length):
        object.__init__(self)
        self.stream = stream
        self.length = int(length)
        self.stream.block(self)

    def dump_length(self):
        return self.length

    def __iter__(self):
        return self

    def __next__(self):
        if self.length == 0:
            raise StopIteration

        readSize = min(self.length, self.CHUNK_SIZE)
        data = self.stream.read(readSize, self)
        self.length -= len(data)
        if self.length == 0:
            self.stream.unblock(self)

        if len(data) != readSize:
            self.stream.error("failed to read content")
        return data
    next = __next__

    def discard(self):
        for data in self:
            pass

    def write(self, stream):
        for data in self:
            stream.write(data)

    @staticmethod
    def read(stream, length):
        return Content(stream, length)
