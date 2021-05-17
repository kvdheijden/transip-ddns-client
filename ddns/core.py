from ddns.provider import DDNSProvider
from ddns.utils import graceful_exit

import requests
import time
import logging

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
    return requests.get('https://api.ipify.org/').text


def ddns_main(domain: AnyStr, dns: List[Dict], provider: DDNSProvider):
    validate_dns_entries(dns)
    current_ip = ''

    with graceful_exit() as g:
        while not g.triggered:
            try:
                new_ip = get_external_ip()
            except Exception as ex:
                logging.exception('Failed to retrieve external IP address', exc_info=(type(ex), ex, ex.__traceback__))
                logging.info('Retrying in 5 seconds...')
                time.sleep(5)
                continue

            if new_ip != current_ip:
                logging.info(f'New IP address retrieved: {new_ip}')

                try:
                    provider.update(current_ip, new_ip, domain, dns)
                except Exception as ex:
                    logging.exception('Failed to update IP address', exc_info=(type(ex), ex, ex.__traceback__))
                    logging.info('Retrying in 5 seconds...')
                    time.sleep(5)
                    continue

                logging.info('IP address updated successfully')
                current_ip = new_ip

            time.sleep(60)
