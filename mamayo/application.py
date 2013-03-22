from collections import defaultdict
from datetime import datetime

from twisted.internet import reactor
from twisted.web.proxy import ReverseProxyResource
from twisted.web.resource import Resource, NoResource, ErrorPage

from mamayo.errors import NoSuchApplicationError
from mamayo.process_herding import GunicornProcessProtocol

_no_resource = NoResource()
_app_down = ErrorPage(
    503, 'Backend Starting',
    "The backend for this application is starting up; try again soon.")
_app_failing = ErrorPage(
    503, 'Backend Failing',
    "The backend for this application is failing to start.")

class MamayoChildApplication(object):
    # Number of seconds in each histogram bit
    HISTOGRAM_BUCKET_SIZE = 10

    def __init__(self, path, name, mount_url='/', log_path=None):
        self.path = path
        self.name = name
        self.mount_url = mount_url
        self.log_path = log_path
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
        if self.runner is not None and self.runner.failure_count > 0:
            return _app_failing
        elif self.runner_port is None:
            return _app_down
        else:
            self.log_request()
            return ReverseProxyResource('localhost', self.runner_port, self.mount_url)

    def round_time(self, dt):
        """Round a time to the nearest histogram point."""
        return dt.replace(
            microsecond=0,
            second=dt.second - dt.second % self.HISTOGRAM_BUCKET_SIZE)

    def log_request(self):
        """Remember that a request happened, like, right now."""
        # TODO candidate for breaking out into a (more persistent) stats object
        # once we know what all this is going to do
        self.requests_finished += 1
        now = self.round_time(datetime.utcnow())
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
        return self.runner_port is not None

    @property
    def failing(self):
        return self.runner is not None and self.runner.failure_count > 0

    @property
    def failed(self):
        return self.runner is not None and self.runner.failure_throttled

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
