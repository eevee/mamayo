from mamayo.application import MamayoDispatchResource
from mamayo.discovery import ApplicationRegistry
from mamayo.status import MamayoStatusResource

from twisted.application import service, internet
from twisted.python.filepath import FilePath
from twisted.web.resource import Resource
from twisted.web.server import Site

import os.path

registry = ApplicationRegistry(
    FilePath(os.path.expanduser('~/.mamayo/public_wsgi')))
registry.scan_and_watch()
root = MamayoDispatchResource(registry)
well_known = Resource()
root.putChild('.well-known', well_known)
well_known.putChild('mamayo', MamayoStatusResource(registry))
site = Site(root)

application = service.Application('mamayo')
internet.TCPServer(8080, site).setServiceParent(application)
