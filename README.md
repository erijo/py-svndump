py-svndump
==========

py-svndump is a python module (named svndump) for parsing and altering the
output from `svnadmin dump` before loading it into a repository with `svnadmin
load`.

The reason it exists was that I needed a way to filter out svn:mergeinfo from a
huge dump-file before loading it to make the size of the repository smaller.

See `parser` for a simple skeleton for reading a dump file from standard input
and writing it unaltered to standard output.

By adding the following to the for-loop we can change the author for all
commits done by "erik" to "erijo" and delete all mergeinfo.

    if isinstance(record, RevisionRecord):
        try:
            if record.properties["svn:author"] == "erik":
                record.properties["svn:author"] = "erijo"
        except KeyError:
            assert record.headers[record.REVISION_NUMBER_HEADER] == "0"
    elif (isinstance(record, NodeRecord)
          and record.properties is not None):
        try:
            del record.properties["svn:mergeinfo"]
        except KeyError:
            pass
