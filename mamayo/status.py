from twisted.web.resource import Resource, NoResource
from twisted.web.template import tags, renderElement

class ApplicationStatusResource(Resource):
    def __init__(self, application):
        Resource.__init__(self)
        self.application = application

    def render_GET(self, request):
        app = self.application
        body = tags.body(
            tags.h1(app.name),
            tags.dl(
                tags.dt('Location'),
                tags.dd(app.path.path),
                tags.dt('Status'),
                tags.dd('Running' if app.running else 'Not running')),
            tags.form(
                tags.button('Respawn runner', name='action', value='respawn'),
                method='post',
                action=''))
        return renderElement(request, body)

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

    def getChild(self, name, request):
        app = self.registry.application_name_map.get(name)
        if app is None:
            return NoResource()
        return ApplicationStatusResource(app)
