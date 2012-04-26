from .section import *

class Record(object):
    def __init__(self, headers):
        object.__init__(self)
        self.headers = headers

    def discard(self):
        pass

    def write(self, stream):
        self.headers.write(stream)

    @staticmethod
    def read(stream):
        headers = HeaderSection.read(stream)
        if headers is None:
            return None

        if NodeRecord.NODE_PATH_HEADER in headers:
            return NodeRecord.read(headers, stream)
        elif RevisionRecord.REVISION_NUMBER_HEADER in headers:
            return RevisionRecord.read(headers, stream)
        elif VersionStampRecord.VERSION_HEADER in headers:
            return VersionStampRecord.read(headers, stream)
        elif UuidRecord.UUID_HEADER in headers:
            return UuidRecord.read(headers, stream)

        stream.error("unknown record %s" % headers[0].key);

class VersionStampRecord(Record):
    VERSION_HEADER = "SVN-fs-dump-format-version"

    def __init__(self, headers):
        Record.__init__(self, headers)
        version = self.headers[self.VERSION_HEADER]
        if int(version) < 2:
            raise ValueError("unknown version '%s'" % version)

    @staticmethod
    def read(headers, stream):
        return VersionStampRecord(headers)

class UuidRecord(Record):
    UUID_HEADER = "UUID"

    def __init__(self, headers):
        Record.__init__(self, headers)

    @staticmethod
    def read(headers, stream):
        return UuidRecord(headers)

class RevisionRecord(Record):
    REVISION_NUMBER_HEADER = "Revision-number"
    PROP_CONTENT_LENGTH = "Prop-content-length"
    CONTENT_LENGTH = "Content-length"

    def __init__(self, headers, properties):
        Record.__init__(self, headers)
        self.properties = properties

    def write(self, stream):
        prop_length = len(self.properties)
        self.headers[self.PROP_CONTENT_LENGTH] = prop_length
        self.headers[self.CONTENT_LENGTH] = prop_length

        Record.write(self, stream)
        self.properties.write(stream)
        stream.writeline()

    @staticmethod
    def read(headers, stream):
        properties = PropertySection.read(stream)
        return RevisionRecord(headers, properties)

class NodeRecord(Record):
    NODE_PATH_HEADER = "Node-path"
    NODE_KIND = "Node-kind"
    NODE_ACTION = "Node-action"
    NODE_COPYFROM_REV = "Node-copyfrom-rev"
    NODE_COPYFROM_PATH = "Node-copyfrom-path"
    TEXT_COPY_SOURCE_MD5 = "Text-copy-source-md5"
    TEXT_CONTENT_MD5 = "Text-content-md5"
    TEXT_CONTENT_LENGTH = "Text-content-length"
    PROP_CONTENT_LENGTH = "Prop-content-length"
    CONTENT_LENGTH = "Content-length"

    # New in version 3
    TEXT_DELTA = "Text-delta"
    PROP_DELTA = "Prop-delta"
    TEXT_DELTA_BASE_MD5 = "Text-delta-base-md5"
    TEXT_DELTA_BASE_SHA1 = "Text-delta-base-sha1"
    TEXT_COPY_SOURCE_SHA1 = "Text-copy-source-sha1"
    TEXT_CONTENT_SHA1 = "Text-content-sha1"

    def __init__(self, headers, properties, content):
        Record.__init__(self, headers)
        self.properties = properties
        self.content = content

    def discard(self):
        if self.content is not None:
            self.content.discard()

    def write(self, stream):
        prop_length = 0
        if self.properties is not None:
            prop_length = len(self.properties)
            self.headers[self.PROP_CONTENT_LENGTH] = prop_length

        text_length = 0
        if self.content is not None:
            text_length = len(self.content)
            self.headers[self.TEXT_CONTENT_LENGTH] = text_length

        if self.properties is not None or self.content is not None:
            self.headers[self.CONTENT_LENGTH] = prop_length + text_length

        Record.write(self, stream)

        if self.properties is not None:
            self.properties.write(stream)

        if self.content is not None:
            self.content.write(stream)

        stream.writeline()
        stream.writeline()

    @staticmethod
    def read(headers, stream):
        properties = None
        if NodeRecord.PROP_CONTENT_LENGTH in headers:
            properties = PropertySection.read(stream)

        content = None
        if NodeRecord.TEXT_CONTENT_LENGTH in headers:
            content = Content.read(
                stream, headers[NodeRecord.TEXT_CONTENT_LENGTH])

        return NodeRecord(headers, properties, content)
