from mamayo.application import MamayoApplication

import operator

class NoSuchApplicationError(Exception):
    "No application could be found with the specified criteria."

def is_not_application(path):
    return not path.child('application.wsgi').exists()

class Explorer(object):
    "I discover mamayo applications."

    def __init__(self, wsgi_root):
        self.wsgi_root = wsgi_root
        self.applications = set()

    def explore(self):
        self.applications = set()
        for path in self.wsgi_root.walk(is_not_application):
            if is_not_application(path):
                continue
            segments_between = path.segmentsFrom(self.wsgi_root)
            app = MamayoApplication(path, segments_between)
            self.applications.add(app)

    def application_from_segments(self, segments):
        sorted_applications = sorted(
            self.applications, key=operator.attrgetter('segment_count'), reverse=True)
        for app in sorted_applications:
            truncated_segments = segments[:app.segment_count]
            if truncated_segments == app.leading_segments:
                return app
        raise NoSuchApplicationError()
