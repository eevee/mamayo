import yaml

class MamayoApplication(object):
    def __init__(self, path):
        self.path = path
        self.config = {}

    def load_config(self):
        with self.path.child('mamayo.conf').open() as infile:
            self.config = yaml.safe_load(infile)
