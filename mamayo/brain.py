from mamayo.application import MamayoDispatchResource
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

        self.registry = ApplicationRegistry(self.wsgi_root)
        self.web_root = MamayoDispatchResource(self.registry)
        self.status_resource = MamayoStatusResource(self.registry)

        if include_status:
            well_known = Resource()
            self.web_root.putChild('.well-known', well_known)
            well_known.putChild('mamayo', self.status_resource)

        self.web_site = Site(self.web_root)

    def startService(self):
        service.MultiService.startService(self)
        self.registry.scan_and_watch()
