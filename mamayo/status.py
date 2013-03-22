from twisted.web.resource import Resource, NoResource
from twisted.web.template import tags, renderElement

class ApplicationStatusResource(Resource):
    def __init__(self, application):
        Resource.__init__(self)
        self.application = application

    def render_GET(self, request):
        body = tags.body(tags.p(repr(self.application)))
        return renderElement(request, body)

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
