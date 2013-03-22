from twisted.web.resource import Resource
from twisted.web.template import tags, renderElement

class ApplicationStatusResource(Resource):
    def __init__(self, explorer):
        Resource.__init__(self)
        self.explorer = explorer

    def render_GET(self, request):
        body = tags.body(
            tags.p('Here are your applications:'),
            tags.ul(*[tags.li(app.path.path) for app in self.explorer.applications]))
        return renderElement(request, body)
