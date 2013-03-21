"Minimal implementations of IFilePath."

import StringIO
import errno

class NonextantThing(object):
    def open(self, mode='r'):
        raise IOError(errno.ENOENT, 'no such file or directory')
    isdir = open

    def exists(self):
        return False

    def child(self, path):
        return self

    def walk(self, descend=None):
        return [self]

    def segmentsFrom(self, ancestor):
        raise ValueError('segmentsFrom on nonextant thing')

_nonextant = NonextantThing()

class File(object):
    def __init__(self, contents):
        self.contents = contents

    def open(self, mode='r'):
        if self.contents is None:
            raise IOError(errno.ENOENT, 'no such file or directory')
        return StringIO.StringIO(self.contents)

    def isdir(self):
        return False

    def exists(self):
        return self.contents is not None

    def child(self, path):
        return _nonextant

    def walk(self, descend=None):
        return [self]

    def segmentsFrom(self, ancestor):
        return ancestor._segmentsTo(self)

    def _segmentsTo(self, descendant):
        if self is descendant:
            return []
        else:
            raise ValueError()

class Directory(object):
    def __init__(self, contents):
        self.contents = contents

    def open(self, mode='r'):
        raise IOError(errno.EISDIR, 'this is a directory')

    def isdir(self):
        return True
    exists = isdir

    def child(self, path):
        return self.contents.get(path, _nonextant)

    def walk(self, descend=None):
        yield self
        for child in self.contents.itervalues():
            if descend is None or descend(child):
                for subchild in child.walk(descend):
                    yield subchild
            else:
                yield child

    def segmentsFrom(self, ancestor):
        return ancestor._segmentsTo(self)

    def _segmentsTo(self, descendant):
        if self is descendant:
            return []
        for name, child in self.contents.iteritems():
            try:
                segments_above = child._segmentsTo(descendant)
            except ValueError:
                pass
            else:
                return [name] + segments_above
        raise ValueError()
