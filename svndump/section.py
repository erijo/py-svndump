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

class Property:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __len__(self):
        length = len("X %d\n" % len(self.key)) + len(self.key) + 1
        if self.value is not None:
            length += len("V %d\n" % len(self.value)) + len(self.value) + 1
        return length

    def write(self, stream):
        if self.value is None:
            stream.writeline("D %d" % len(self.key))
        else:
            stream.writeline("K %d" % len(self.key))
        stream.write(self.key)
        stream.writeline()

        if self.value is not None:
            stream.writeline("V %d" % len(self.value))
            stream.write(self.value)
            stream.writeline()

    @staticmethod
    def read(stream):
        line = stream.readline()
        if line == PropertySection.PROPS_END:
            return None

        if (line[0] != 'K' and line[0] != 'D'):
            stream.error("invalid property key line")

        def read_segment(stream, line):
            length = int(line[2:])
            segment = stream.read(length)
            if len(segment) != length:
                stream.error("incorrect property length '%s'" % length)
            stream.readline()
            return segment

        key = read_segment(stream, line)

        value = None
        if line[0] == 'K':
            line = stream.readline()
            if line[0] != 'V':
                stream.error("invalid property value line")
            value = read_segment(stream, line)

        return Property(key, value)

class PropertySection(object):
    PROPS_END = "PROPS-END"

    def __init__(self, properties):
        object.__init__(self)
        self.properties = properties

    def __len__(self):
        length = len(self.PROPS_END) + 1
        for property in self.properties:
            length += len(property)
        return length

    def __iter__(self):
        return iter(self.properties)

    def __delitem__(self, key):
        for property in self.properties:
            if property.key == key:
                self.properties.remove(property)
                return
        raise KeyError(key)

    def write(self, stream):
        for property in self.properties:
            property.write(stream)
        stream.writeline("%s" % self.PROPS_END)

    @staticmethod
    def read(stream):
        properties = []
        while True:
            property = Property.read(stream)
            if property is None:
                break
            properties.append(property)
        return PropertySection(properties)

class Content(object):
    CHUNK_SIZE = 2048

    def __init__(self, stream, length):
        object.__init__(self)
        self.stream = stream
        self.length = int(length)
        self.stream.block(self)

    def __len__(self):
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
