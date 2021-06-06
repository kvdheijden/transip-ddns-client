import signal
import threading
from typing import Iterable


class graceful_exit(object):
    def __init__(self, signals: Iterable = (signal.SIGINT, signal.SIGTERM)):
        self.signum = 0
        self._event = threading.Event()
        self._signals = signals
        self._signal_handlers = {}

    def __enter__(self):
        for s in self._signals:
            self._signal_handlers[s] = signal.signal(s, self._handler)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for s in self._signals:
            signal.signal(s, self._signal_handlers[s])

    def _handler(self, signum, _frame):
        self.signum = signum
        self._event.set()

    @property
    def trigger(self):
        return self._event
