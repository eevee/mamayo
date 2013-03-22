from mamayo.brain import Brain

from twisted.application import service, internet
from twisted.python.filepath import FilePath

import os.path

application = service.Application('mamayo')
brain = Brain(FilePath(os.path.expanduser('~/.mamayo')))
brain.setServiceParent(application)
internet.TCPServer(8080, brain.web_site).setServiceParent(brain)
