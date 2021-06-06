import abc
import netifaces
import requests
from datetime import datetime, timedelta
from typing import AnyStr, Tuple, Dict
import warnings


class ExternalIPSource(abc.ABC):
    @abc.abstractmethod
    def get(self):
        raise NotImplementedError()


class WanIPSource(ExternalIPSource):
    def __init__(self, ifname: AnyStr, ipv6: bool = False):
        self.ifname = ifname
        self.ip_type = netifaces.AF_INET6 if ipv6 else netifaces.AF_INET

    def get(self):
        if_addresses = netifaces.ifaddresses(self.ifname)
        interface = if_addresses[self.ip_type][0]
        return interface['addr']


class RoundRobinRequestsIPSource(ExternalIPSource):
    def __init__(self):
        now = datetime.now()

        self.ip_sources = {
            'ipify': {
                'fcn': lambda: requests.get('https://api.ipify.org/').text.strip(),
                'last': now
            },
            'checkip (amazonaws)': {
                'fcn': lambda: requests.get('https://checkip.amazonaws.com').text.strip(),
                'last': now
            },
            'wikipedia': {
                'fcn': lambda: requests.get('https://www.wikipedia.org').headers['X-Client-IP'].strip(),
                'last': now
            },
            'ipinfo': {
                'fcn': lambda: requests.get('http://ipinfo.io/json').json()['ip'].strip(),
                'last': now
            },
        }

    @staticmethod
    def parse_ip(ip: AnyStr) -> Tuple[int, int, int, int]:
        n0, n1, n2, n3 = ip.split('.')
        n0, n1, n2, n3 = int(n0), int(n1), int(n2), int(n3)
        if n0 not in range(256):
            raise ValueError('First IP address nibble invalid')
        elif n1 not in range(256):
            raise ValueError('Second IP address nibble invalid')
        elif n2 not in range(256):
            raise ValueError('Third IP address nibble invalid')
        elif n3 not in range(256):
            raise ValueError('Fourth IP address nibble invalid')
        return n0, n1, n2, n3

    def get_by_source(self, ip_source: Dict) -> Tuple[int, int, int, int]:
        ip = ip_source['fcn']()
        ip = self.parse_ip(ip)
        return ip

    def get(self) -> Tuple[int, int, int, int]:
        now = datetime.now()
        key = sorted(self.ip_sources.keys(), key=lambda k: self.ip_sources[k]['last'])[0]
        if self.ip_sources[key]['last'] > now:
            raise ValueError('All IP sources timed out')

        try:
            ip = self.get_by_source(self.ip_sources[key])
            self.ip_sources[key]['last'] = now
            return ip
        except ValueError:
            warnings.warn(RuntimeWarning(f'Ip source \"{key}\" timed out for 30 minutes.'))
            self.ip_sources[key]['last'] = now + timedelta(minutes=30)
            return self.get()
