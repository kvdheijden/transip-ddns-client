from ddns.provider import DDNSProvider
from ddns.utils import graceful_exit

import requests
import logging
import random

from typing import AnyStr, List, Dict


def validate_dns_entries(dns: List[Dict]) -> None:
    if not isinstance(dns, list):
        raise TypeError('DNS not of type \'list\'')

    for entry in dns:
        if not isinstance(entry, dict):
            raise TypeError('DNS entry not of type \'dict\'')

        test = {
            'name': False,
            'expire': False,
            'type': False,
            'content': False
        }

        for key in entry:
            if key in test:
                test[key] = True
            else:
                raise TypeError(f'DNS entry does not have field called \'{key}\'')

        for key in test:
            if not test[key]:
                raise TypeError(f'DNS entry must have field called \'{key}\'')


def get_external_ip() -> AnyStr:
    choices = {
        'ipify': lambda: requests.get('https://api.ipify.org/').text.strip(),
        'ident.me': lambda: requests.get('https://ident.me/').text.strip(),
        'checkip (amazonaws)': lambda: requests.get('https://checkip.amazonaws.com').text.strip(),
        'wikipedia': lambda: requests.get('https://www.wikipedia.org').headers['X-Client-IP'].strip(),
        'ipinfo': lambda: requests.get('http://ipinfo.io/json').json()['ip'].strip(),
    }
    key = random.choice(list(choices.keys()))
    logging.debug(f'Retrieving IP address from {key}')
    return choices[key]()


def ddns_main(domain: AnyStr, dns: List[Dict], provider: DDNSProvider):
    validate_dns_entries(dns)
    current_ip = ''

    with graceful_exit() as g:
        while not g.trigger.is_set():
            try:
                new_ip = get_external_ip()
            except Exception as ex:
                logging.exception('Failed to retrieve external IP address', exc_info=(type(ex), ex, ex.__traceback__))
                logging.info('Retrying in 5 seconds...')
                g.trigger.wait(5)
                continue

            if new_ip != current_ip:
                logging.info(f'New IP address retrieved: {new_ip}')

                try:
                    provider.update(current_ip, new_ip, domain, dns)
                except Exception as ex:
                    logging.exception('Failed to update IP address', exc_info=(type(ex), ex, ex.__traceback__))
                    logging.info('Retrying in 5 seconds...')
                    g.trigger.wait(5)
                    continue

                logging.info('IP address updated successfully')
                current_ip = new_ip

            g.trigger.wait(30)
