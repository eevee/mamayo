from calendar import timegm
from datetime import datetime, timedelta
import json

from mako.lookup import TemplateLookup

from twisted.python.filepath import FilePath
from twisted.web.resource import Resource, NoResource
from twisted.web.static import File
from twisted.web.template import tags, renderElement

LOOKUP = TemplateLookup(
    directories=[
        FilePath(__file__).sibling('templates').path,
    ],
    output_encoding='utf8',
)

def build_flot_data(app):
    # Build a flot-compatible JSON blob
    flot_data = []
    flot_series = dict(
        data=flot_data,
        label='Request count',
    )

    time = app.round_time(datetime.utcnow())
    dt = timedelta(seconds=app.HISTOGRAM_BUCKET_SIZE)
    for _ in range(30):
        flot_data.append([
            timegm(time.timetuple()) * 1000,
            app.request_histogram.get(time, 0),
        ])

        time -= dt
    flot_data.reverse()

    return [flot_series]

class ApplicationHistogramResource(Resource):
    def __init__(self, application):
        Resource.__init__(self)
        self.application = application

    def render_GET(self, request):
        request.setHeader('Content-Type', 'text/json')

        return json.dumps(build_flot_data(self.application))

class ApplicationStatusResource(Resource):
    def __init__(self, application):
        Resource.__init__(self)
        self.application = application

    def getChild(self, name, request):
        if name == 'log' and self.application.log_path is not None:
            return File(self.application.log_path.path, 'text/plain; charset=utf8')
        elif name == 'chartdata.json':
            return ApplicationHistogramResource(self.application)
        return NoResource()

    def render_GET(self, request):
        app = self.application

        log_size = None
        if self.application.log_path is not None:
            log_size = self.application.log_path.getsize()

        return LOOKUP.get_template('app-status.mako').render(
            request=request,
            app=app,
            flot_data=json.dumps(build_flot_data(app)),
            log_size=log_size,
        )

    def render_POST(self, request):
        action = request.args.get('action', [None])[0]
        if action == 'respawn':
            self.application.respawn_runner()
        return self.render_GET(request)

class ApplicationListResource(Resource):
    def __init__(self, registry):
        Resource.__init__(self)
        self.registry = registry

    def render_GET(self, request):
        applications = []
        for app in self.registry.applications.values():
            link = tags.a(tags.tt(app.name), ' at ', tags.tt(app.path.path),
                          href=app.name)
            applications.append(tags.li(link))

        body = tags.body(
            tags.p('Here are your applications:'),
            tags.ul(*applications))
        return renderElement(request, body)

class MamayoStatusResource(Resource):
    def __init__(self, registry):
        Resource.__init__(self)
        self.registry = registry
        self.putChild('', ApplicationListResource(self.registry))
        self.putChild('static', File(FilePath(__file__).sibling('static').path))

    def getChild(self, name, request):
        app = self.registry.application_name_map.get(name)
        if app is None:
            return NoResource()
        return ApplicationStatusResource(app)
