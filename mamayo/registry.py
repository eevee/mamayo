from itertools import chain

from mamayo.application import MamayoChildApplication
from mamayo.errors import NoSuchApplicationError

from twisted.internet.inotify import INotify
from twisted.internet.inotify import (
    IN_CREATE, IN_MOVED_TO,
    IN_DELETE, IN_MOVED_FROM, IN_DELETE_SELF, IN_MOVE_SELF, IN_UNMOUNT)
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
        for path in self.wsgi_root.walk(is_not_application):
            if is_not_application(path):
                continue
            self.register(path)

    def watch(self):
        notifier = INotify()
        notifier.startReading()
        notifier.watch(self.wsgi_root,
            IN_CREATE | IN_MOVED_TO | IN_DELETE | IN_MOVED_FROM | IN_DELETE_SELF | IN_MOVE_SELF | IN_UNMOUNT,
            callbacks=[self.on_fs_change], autoAdd=True, recursive=True)

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
                self.applications[key].destroy()
                del self.applications[key]

    def application_from_segments(self, segments):
        app = self.applications.get(tuple(segments))
        if app is None:
            raise NoSuchApplicationError()
        return app
