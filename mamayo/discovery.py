from mamayo.application import MamayoChildApplication
from mamayo.errors import NoSuchApplicationError

def is_not_application(path):
    return not path.child('application.wsgi').exists()

class Explorer(object):
    "I discover mamayo applications."

    def __init__(self, wsgi_root):
        self.wsgi_root = wsgi_root
        self.applications = set()
        self.segments_to_application_map = {}

    def explore(self):
        self.applications = set()
        for path in self.wsgi_root.walk(is_not_application):
            if is_not_application(path):
                continue
            segments_between = path.segmentsFrom(self.wsgi_root)
            app = MamayoChildApplication(path)
            self.segments_to_application_map[tuple(segments_between)] = app
            self.applications.add(app)

    def application_from_segments(self, segments):
        app = self.segments_to_application_map.get(tuple(segments))
        if app is None:
            raise NoSuchApplicationError()
        return app
