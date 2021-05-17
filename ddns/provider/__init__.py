import abc
from typing import AnyStr, List, Dict

__all__ = ['DDNSProvider']


class DDNSProvider(abc.ABC):
    @abc.abstractmethod
    def update(self, current_ip: AnyStr, new_ip: AnyStr, domain: AnyStr, dns: List[Dict]) -> None:
        raise NotImplementedError()
