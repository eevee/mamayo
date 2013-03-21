from mamayo.application import MamayoApplication

class Explorer(object):
    "I discover mamayo applications."

    def __init__(self, wsgi_root):
        self.wsgi_root = wsgi_root
        self.applications = set()

    def explore(self):
        self.applications = set()
        for path in self.wsgi_root.walk():
            conf = path.child('mamayo.conf')
            if not conf.exists():
                continue
            app = MamayoApplication(path)
            self.applications.add(app)
