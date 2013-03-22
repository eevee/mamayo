from mamayo.application import MamayoDispatchResource
from mamayo.discovery import Explorer
from mamayo.status import MamayoStatusResource

from twisted.application import service, internet
from twisted.python.filepath import FilePath
from twisted.web.resource import Resource
from twisted.web.server import Site

import os.path

e = Explorer(FilePath(os.path.expanduser('~/.mamayo/public_wsgi')))
e.explore()
root = MamayoDispatchResource(e)
well_known = Resource()
root.putChild('.well-known', well_known)
well_known.putChild('mamayo', MamayoStatusResource(e))
site = Site(root)

application = service.Application('mamayo')
internet.TCPServer(8080, site).setServiceParent(application)
