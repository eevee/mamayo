from mamayo.errors import NoSuchApplicationError

from twisted.web.resource import Resource, NoResource
from twisted.web.static import Data

class MamayoApplication(object):
    def __init__(self, path):
        self.path = path

    def as_resource(self):
        return Data(repr(self.path), 'text/plain')

_no_resource = NoResource()

class MamayoDispatchResource(Resource):
    def __init__(self, explorer):
        Resource.__init__(self)
        self.explorer = explorer

    def _application_resource_from_segments(self, segments, default):
        segments = tuple(segments)
        try:
            app = self.explorer.application_from_segments(segments)
        except NoSuchApplicationError:
            return default
        else:
            return app.as_resource()

    def render(self, request):
        resource = self._application_resource_from_segments(
            request.prepath, _no_resource)
        return resource.render(request)

    def getChild(self, name, request):
        return self._application_resource_from_segments(request.prepath, self)
