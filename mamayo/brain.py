from mamayo.application import MamayoDispatchResource, MamayoChildApplication
from mamayo.registry import ApplicationRegistry
from mamayo.status import MamayoStatusResource

from twisted.application import service
from twisted.web.resource import Resource
from twisted.web.server import Site

class Brain(service.MultiService):
    def __init__(self, mamayo_root, wsgi_root=None, include_status=True):
        service.MultiService.__init__(self)

        self.mamayo_root = mamayo_root
        if wsgi_root is None:
            wsgi_root = self.mamayo_root.child('public_wsgi')
        self.wsgi_root = wsgi_root
        self.log_root = self.mamayo_root.child('logs')
        if not self.log_root.exists():
            self.log_root.createDirectory()

        self.registry = ApplicationRegistry(self.wsgi_root)
        self.registry.application_factory = self.create_application
        self.web_root = MamayoDispatchResource(self.registry)
        self.status_resource = MamayoStatusResource(self.registry)

        if include_status:
            well_known = Resource()
            self.web_root.putChild('.well-known', well_known)
            well_known.putChild('mamayo', self.status_resource)

        self.web_site = Site(self.web_root)

    def create_application(self, path, name):
        app_log_directory = self.log_root.child(name)
        if not app_log_directory.exists():
            app_log_directory.createDirectory()
        app_log = app_log_directory.child('current')
        return MamayoChildApplication(path, name, app_log)

    def startService(self):
        service.MultiService.startService(self)
        self.registry.scan_and_watch()
