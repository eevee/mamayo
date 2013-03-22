from collections import defaultdict
from datetime import datetime

from twisted.internet import reactor
from twisted.web.proxy import ReverseProxyResource
from twisted.web.resource import Resource, NoResource

from mamayo.errors import NoSuchApplicationError
from mamayo.process_herding import GunicornProcessProtocol

_no_resource = NoResource()

class MamayoChildApplication(object):
    def __init__(self, path, name):
        self.path = path
        self.name = name
        self.runner = None
        self.runner_port = None

        # Stat tracking
        self.requests_finished = 0
        self.request_histogram = defaultdict(int)

    def spawn_runner(self):
        """Run the WSGI runner in a child process."""
        # TODO sooo if the process dies, it should restart, /but/ it should
        # avoid an awful restart loop.  **AND** it should log the failure
        # somewhere and the 404 should change to match.
        if self.runner is None:
            self.runner = GunicornProcessProtocol(self, self.path, reactor)
        self.runner.spawn()

    def respawn_runner(self):
        if self.runner is None:
            self.spawn_runner()
        else:
            self.runner.respawn()

    def as_resource(self):
        # TODO there's a delay before gunicorn actually finishes starting; Do
        # Something in the meantime?
        if self.runner_port is None:
            # TODO should distinguish this from a 404: either the child has yet
            # to start, or it /won't/ start, or we don't recognize this
            # endpoint as a wsgi app
            return _no_resource
        else:
            self.log_request()
            return ReverseProxyResource('localhost', self.runner_port, "/")

    def log_request(self):
        """Remember that a request happened, like, right now."""
        # TODO candidate for breaking out into a (more persistent) stats object
        # once we know what all this is going to do
        self.requests_finished += 1
        now = datetime.utcnow()
        now = now.replace(microsecond=0, second=now.second - now.second % 30)
        self.request_histogram[now] += 1

    def destroy(self):
        """Kill me off!"""
        # TODO should this wait X time for the child to perhaps finish handling
        # its requests?
        if self.runner is not None:
            self.runner.destroy()
            self.runner_port = None

    @property
    def running(self):
        return self.runner is not None and self.runner.running


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
