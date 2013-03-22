from itertools import chain

from mamayo.application import MamayoChildApplication
from mamayo.errors import NoSuchApplicationError
from mamayo.util import SoftHardScheduler

try:
    from twisted.internet.inotify import INotify
    from twisted.internet.inotify import (
        IN_CREATE, IN_MOVED_TO,
        IN_DELETE, IN_MOVED_FROM, IN_DELETE_SELF, IN_MOVE_SELF, IN_UNMOUNT)
except ImportError:
    INotify = None

from twisted.internet import task, reactor
from twisted.python import log

def looks_like_application(path):
    return path.child('application.py').exists()

def is_not_application(path):
    return not looks_like_application(path)

class ApplicationRegistry(object):
    """I track all the known applications."""

    application_factory = MamayoChildApplication
    poll_interval = 5
    rescan_soft_delay = 5
    rescan_hard_delay = 20

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
            self._scheduler = SoftHardScheduler(
                reactor, self.rescan_soft_delay, self.rescan_hard_delay, self.scan)
            notifier = INotify()
            notifier.startReading()
            notifier.watch(self.wsgi_root,
                IN_CREATE | IN_MOVED_TO | IN_DELETE | IN_MOVED_FROM | IN_DELETE_SELF | IN_MOVE_SELF | IN_UNMOUNT,
                callbacks=[self.on_fs_change], autoAdd=True, recursive=True)
    else:
        def watch(self):
            self._scan_looper = task.LoopingCall(self.scan)
            self._scan_looper.start(self.poll_interval)

    def _debug_notify(self, notifier, path, mask):
        from twisted.internet.inotify import humanReadableMask
        print path, humanReadableMask(mask)

    def register(self, path):
        log.msg("Registering child application at", path)
        key = tuple(path.segmentsFrom(self.wsgi_root))
        name = '.'.join(['root'] + [segment.replace('.', '..') for segment in key])
        mount_url = '/'.join(('',) + key)

        if key in self.applications:
            self._unregister_by_key(key)

        assert name not in self.application_name_map
        app = self.application_factory(path=path, name=name, mount_url=mount_url)
        self.applications[key] = app
        self.application_name_map[name] = app
        app.spawn_runner()

    def unregister(self, path):
        key = tuple(path.segmentsFrom(self.wsgi_root))
        self._unregister_by_key(key)

    def _unregister_by_key(self, key):
        app = self.applications[key]
        self.applications[key].destroy()
        del self.applications[key]
        del self.application_name_map[app.name]

    def on_fs_change(self, notifier, path, mask):
        self._scheduler.schedule()

    def application_from_segments(self, segments):
        app = self.applications.get(tuple(segments))
        if app is None:
            raise NoSuchApplicationError()
        return app
