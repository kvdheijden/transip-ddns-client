import signal

from typing import Dict


class graceful_exit(object):
    def __init__(self, signals=(signal.SIGINT, signal.SIGTERM)):
        self.signum = 0
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

    @property
    def triggered(self):
        return bool(self.signum)


def compare_dns(a: Dict, b: Dict):
    return a['name'] == b['name'] and \
           a['type'] == b['type']
