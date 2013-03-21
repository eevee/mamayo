import yaml

class MamayoApplication(object):
    def __init__(self, path, leading_segments):
        self.path = path
        self.leading_segments = leading_segments
        self.config = {}

    @property
    def segment_count(self):
        return len(self.leading_segments)

    def load_config(self):
        with self.path.child('mamayo.conf').open() as infile:
            self.config = yaml.safe_load(infile)

    def as_resource(self):
        return Data(repr(self.config), 'text/plain')
