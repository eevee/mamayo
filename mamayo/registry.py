from itertools import chain

from mamayo.application import MamayoChildApplication
from mamayo.errors import NoSuchApplicationError

try:
    from twisted.internet.inotify import INotify
    from twisted.internet.inotify import (
        IN_CREATE, IN_MOVED_TO,
        IN_DELETE, IN_MOVED_FROM, IN_DELETE_SELF, IN_MOVE_SELF, IN_UNMOUNT)
except ImportError:
    INotify = None

from twisted.internet import task
from twisted.python import log

def looks_like_application(path):
    return path.child('application.py').exists()

def is_not_application(path):
    return not looks_like_application(path)

class ApplicationRegistry(object):
    """I track all the known applications."""

    def __init__(self, wsgi_root):
        self.wsgi_root = wsgi_root
        self.applications = dict()  # segments => child app
        self.application_name_map = {}

    def scan_and_watch(self):
        self.scan()
        self.watch()

    def scan(self):
        new_applications = set()
        old_applications = set(app.path for app in self.applications.itervalues())
        for path in self.wsgi_root.walk():
            if is_not_application(path):
                continue
            new_applications.add(path)

        for path in new_applications - old_applications:
            self.register(path)
        for path in old_applications - new_applications:
            self.unregister(path)

    if INotify is not None:
        def watch(self):
            notifier = INotify()
            notifier.startReading()
            notifier.watch(self.wsgi_root,
                IN_CREATE | IN_MOVED_TO | IN_DELETE | IN_MOVED_FROM | IN_DELETE_SELF | IN_MOVE_SELF | IN_UNMOUNT,
                callbacks=[self.on_fs_change], autoAdd=True, recursive=True)
    else:
        def watch(self):
            self._scan_looper = task.LoopingCall(self.scan)
            self._scan_looper.start(5)

    def _debug_notify(self, notifier, path, mask):
        from twisted.internet.inotify import humanReadableMask
        print path, humanReadableMask(mask)

    def register(self, path):
        log.msg("Registering child application at", path)
        key = tuple(path.segmentsFrom(self.wsgi_root))
        name = '.'.join(['root'] + [segment.replace('.', '..') for segment in key])

        if key in self.applications:
            self.applications[key].destroy()
            del self.applications[key]
            del self.application_name_map[name]

        assert name not in self.application_name_map
        app = MamayoChildApplication(path, name)
        self.applications[key] = app
        self.application_name_map[name] = app
        app.spawn_runner()

    def unregister(self, path):
        key = tuple(path.segmentsFrom(self.wsgi_root))
        app = self.applications[key]
        self.applications[key].destroy()
        del self.applications[key]
        del self.application_name_map[app.name]

    def on_fs_change(self, notifier, path, mask):
        # TODO inotify is hard.  in the case of a move, we only get one
        # event...
        if path.exists():
            # TODO as written, this will reload an app every time every one of
            # its files changes, which is Very Bad when an app is being updated
            for ancestor in chain([path], path.parents()):
                if looks_like_application(ancestor):
                    break
            else:
                return

            self.register(ancestor)
        else:
            if not path.isdir():
                path = path.parent()

            try:
                key = tuple(path.segmentsFrom(self.wsgi_root))
            except ValueError:
                # Either the WSGI root itself, or a parent (somehow!)
                return

            if key in self.applications:
                log.msg("Removing child application at", path)
                self.unregister(path)

    def application_from_segments(self, segments):
        app = self.applications.get(tuple(segments))
        if app is None:
            raise NoSuchApplicationError()
        return app
