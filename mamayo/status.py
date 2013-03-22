from calendar import timegm
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

class ApplicationStatusResource(Resource):
    def __init__(self, application):
        Resource.__init__(self)
        self.application = application

    def getChild(self, name, request):
        if name == 'log' and self.application.log_path is not None:
            return File(self.application.log_path.path, 'text/plain; charset=utf8')
        return NoResource()

    def render_GET(self, request):
        app = self.application

        # Build a flot-compatible JSON blob
        flot_series = dict(
            data=[],
            label='Request count',
        )
        for dt, count in sorted(app.request_histogram.items()):
            flot_series['data'].append([
                timegm(dt.timetuple()) * 1000,
                count,
            ])

        log_size = None
        if self.application.log_path is not None:
            log_size = self.application.log_path.getsize()

        return LOOKUP.get_template('app-status.mako').render(
            request=request,
            app=app,
            flot_data=json.dumps([flot_series]),
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
