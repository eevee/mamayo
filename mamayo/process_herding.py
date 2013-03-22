import os

from twisted.internet.protocol import ProcessProtocol
from twisted.protocols.basic import LineReceiver
from twisted.python.filepath import FilePath

class AdHocCommandParser(LineReceiver):
    """I implement a micro-protocol for communicating with a WSGI runner child.
    I'm pretty terrible, all things considered.
    """

    # LR defaults to \r\n for reasons I can only assume are tequila-related
    delimiter = '\n'

    def __init__(self, protocol):
        # TODO circular ref
        self.protocol = protocol

    def lineReceived(self, line):
        """Dispatches commands from the child.  So far there's only one.  And
        you have to use it.  Or everything dies.
        """
        command, arg = line.split(' ')
        arg = int(arg)
        assert command == 'set-port'

        self.protocol.set_port(arg)


class GunicornProcessProtocol(ProcessProtocol):
    def __init__(self, mamayo_app, path):
        self.mamayo_app = mamayo_app
        self.path = path
        self.entry_point = 'application:application'

        self.line_receiver = AdHocCommandParser(self)

    def spawn(self, reactor):
        # Assemble environment: PYTHONPATH needs to start in the app's root
        env = os.environ.copy()
        pythonpath = self.path.path
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = pythonpath + ':' + env['PYTHONPATH']
        else:
            env['PYTHONPATH'] = pythonpath

        # Spawn us!
        reactor.spawnProcess(
            self,
            'gunicorn',
            ['gunicorn',
                '-c', FilePath(__file__).parent().child('gunicorn_config.conf.py').path,
                self.entry_point,
            ],
            # fd 3 and 4 are used as an out-of-band comm channel
            childFDs={0: 0, 1: 1, 2: 2, 3: "r", 4: "w"},
            env=env,
        )

    def connectionMade(self):
        self.transport.closeStdin()

    def childDataReceived(self, fd, data):
        if fd == 3:
            self.line_receiver.dataReceived(data)
        else:
            super(GunicornProcessProtocol, self).childDataReceived(fd, data)

    def processEnded(self):
        self.mamayo_app.runner_port = None

    def set_port(self, port):
        self.mamayo_app.runner_port = port
