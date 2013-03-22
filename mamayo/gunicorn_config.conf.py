"""Common gunicorn configuration, used by all gunicorn apps.  Most of this is
hooks, not "real" configuration.  See the `mamayo.process_herding` module,
which does the other end of the communication implemented here.
"""

import os

bind = 'localhost:0'

def when_ready(server):
    sockname = server.LISTENERS[0].sock.getsockname()
    port = sockname[1]

    with os.fdopen(3, 'w') as f:
        f.write('set-port %d\n' % port)
