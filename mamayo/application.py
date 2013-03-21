class MamayoApplication(object):
    def __init__(self, path, leading_segments):
        self.path = path
        self.leading_segments = leading_segments

    @property
    def segment_count(self):
        return len(self.leading_segments)

    def as_resource(self):
        return Data(repr(self.config), 'text/plain')
