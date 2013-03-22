import os

from twisted.internet.error import AlreadyCalled
from twisted.internet.protocol import ProcessProtocol
from twisted.protocols.basic import LineReceiver
from twisted.python.filepath import FilePath
from twisted.python import log

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
        args = line.split(' ')
        command = args.pop(0)

        if command == 'set-port':
            port = int(args[0])
            self.protocol.set_port(port)
        elif command == 'request-done':
            self.protocol.track_request_done()
        else:
            log.error("Child is babbling nonsense: {0!r}".format(line))


class GunicornProcessProtocol(ProcessProtocol):
    respawn_delay = 2
    should_respawn = True

    _respawn_delayed_call = None

    def __init__(self, mamayo_app, path, reactor):
        self.mamayo_app = mamayo_app
        self.path = path
        self.reactor = reactor
        self.entry_point = 'application:application'
        self.running = False

        self.line_receiver = AdHocCommandParser(self)

    def _cancel_respawn(self):
        if self._respawn_delayed_call is not None:
            try:
                self._respawn_delayed_call.cancel()
            except AlreadyCalled:
                pass
        self._respawn_delayed_call = None

    def spawn(self):
        if self.running:
            return

        # If we were waiting to respawn, spawn immediately instead
        self._cancel_respawn()

        # Assemble environment: PYTHONPATH needs to start in the app's root
        env = os.environ.copy()
        pythonpath = self.path.path
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = pythonpath + ':' + env['PYTHONPATH']
        else:
            env['PYTHONPATH'] = pythonpath
        env['SCRIPT_NAME'] = self.mamayo_app.mount_url

        # fd 352 and 353 are used as an out-of-band comm channel
        child_fds = {0: 0, 1: 1, 2: 2, 352: "r", 353: "w"}
        if self.mamayo_app.log_path is not None:
            # TODO maybe explicitly close this in the parent instead of relying
            # on gc
            log_file = self.mamayo_app.log_path.open('a')
            child_fds[1] = child_fds[2] = log_file.fileno()

        # Spawn us!
        self.reactor.spawnProcess(
            self,
            'gunicorn',
            ['gunicorn',
                '-c', FilePath(__file__).parent().child('gunicorn_config.conf.py').path,
                self.entry_point,
            ],
            childFDs=child_fds,
            env=env,
        )
        self.running = True

    def respawn(self):
        if self.running:
            self.transport.loseConnection()
            self.transport.signalProcess("TERM")
        else:
            self.spawn()

    def connectionMade(self):
        self.transport.closeStdin()

    def childDataReceived(self, fd, data):
        if fd == 352:
            self.line_receiver.dataReceived(data)
        else:
            ProcessProtocol.childDataReceived(self, fd, data)

    def processEnded(self, reason):
        self.running = False
        self.mamayo_app.runner_port = None
        log.err(reason, 'gunicorn runner for app %s died' % (self.mamayo_app.name,))
        if self.should_respawn:
            log.msg('respawning gunicorn for app %s in %ss' % (self.mamayo_app.name,
                                                               self.respawn_delay))
            self._respawn_delayed_call = self.reactor.callLater(self.respawn_delay, self.spawn)
        else:
            log.msg('not respawning gunicorn for app %s' % (self.mamayo_app.name,))

    def destroy(self):
        self._cancel_respawn()
        self.should_respawn = False
        if not self.running:
            return
        self.transport.loseConnection()
        self.transport.signalProcess("TERM")

    ### Commands passed up from the child process

    def set_port(self, port):
        self.mamayo_app.runner_port = port

    def track_request_done(self):
        # TODO: minor problem here: gunicorn's workers have all their fds
        # closed and can't talk to us.  oops.
        self.mamayo_app.requests_finished += 1
