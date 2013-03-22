from twisted.internet.error import AlreadyCalled, AlreadyCancelled

def quietly_cancel(delayed_call):
    try:
        delayed_call.cancel()
    except (AlreadyCalled, AlreadyCancelled):
        pass

class SoftHardScheduler(object):
    "I schedule events to happen on either a soft or hard delay."

    _delayed_calls = None

    def __init__(self, reactor, soft_delay, hard_delay, callback, *a, **kw):
        self.reactor = reactor
        self.soft_delay = soft_delay
        self.hard_delay = hard_delay
        self.callback = callback
        self.args = a
        self.kwargs = kw

    def schedule(self):
        if self._delayed_calls is None:
            soft_call = self.reactor.callLater(self.soft_delay, self._fire)
            hard_call = self.reactor.callLater(self.hard_delay, self._fire)
            self._delayed_calls = soft_call, hard_call
        else:
            soft_call, _ = self._delayed_calls
            soft_call.reset(self.soft_delay)

    def _fire(self):
        soft_call, hard_call = self._delayed_calls
        self._delayed_calls = None
        quietly_cancel(soft_call)
        quietly_cancel(hard_call)
        self.callback(*self.args, **self.kwargs)
