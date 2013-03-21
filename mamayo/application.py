from mamayo.errors import NoSuchApplicationError

from twisted.web.resource import Resource, NoResource
from twisted.web.static import Data

class MamayoApplication(object):
    def __init__(self, path, leading_segments):
        self.path = path
        self.leading_segments = leading_segments

    @property
    def segment_count(self):
        return len(self.leading_segments)

    def as_resource(self):
        return Data(repr((self.path, self.leading_segments)), 'text/plain')

class MamayoDispatchResource(Resource):
    isLeaf = True

    def __init__(self, explorer):
        Resource.__init__(self)
        self.explorer = explorer

    def render(self, request):
        try:
            app = self.explorer.application_from_segments(request.postpath)
        except NoSuchApplicationError:
            return NoResource().render(request)
        return app.as_resource().render(request)
