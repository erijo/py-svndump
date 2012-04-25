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
            else:
                return None
        if len(headers) == 0:
            return None
        return HeaderSection(headers)

    def __iter__(self):
        return self.headers.__iter__()

    def __getitem__(self, key):
        for header in self.headers:
            if header.key == key:
                return header.value
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
            stream.error("invalid property line")

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
                stream.error("line is not property value")
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

    def __len__(self):
        return self.length

    def write(self, stream):
        while self.length > 0:
            readSize = min(self.length, self.CHUNK_SIZE)
            self.length -= readSize

            data = self.stream.read(readSize)
            stream.write(data)
        empty_line = self.stream.readline()
        stream.writeline()
