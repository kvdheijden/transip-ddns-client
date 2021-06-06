from transipddnsclient import __version__
from transipddnsclient.core import transipddnsclient
from transipddnsclient.transip import TransIPApi
from transipddnsclient.externalip import WanIPSource, RoundRobinRequestsIPSource

import argparse
import configparser
import logging
import sys

from typing import Sequence, Text


class Verbosity(argparse.Action):
    def __init__(self, option_strings: Sequence[Text], dest: Text, **kwargs):
        super().__init__(option_strings, dest, **kwargs)
        self.initial = logging.CRITICAL
        self.v = self.initial
        self._gain = 10

    def __call__(self, parser, args, values, option_string=None):
        if values is None:
            # multiple "-v" flags
            self.v -= self._gain
        else:
            try:
                # Verbosity level specified as integer
                self.v = self.initial - int(values) * self._gain
            except ValueError:
                # String of multiple v's
                self.v = self.initial - (values.count('v') + 1) * self._gain

        if logging.NOTSET > self.v or self.v > logging.CRITICAL:
            parser.error('Verbosity level must be between 0 and 5.')

        setattr(args, self.dest, self.v)


def transipddnsclient_main() -> int:
    # Parse arguments
    parser = argparse.ArgumentParser('python -m transipddnsclient', description='TransIP dDNS Client')
    parser.add_argument('--version',
                        action='version',
                        version=__version__)
    parser.add_argument('-v',
                        nargs='?',
                        action=Verbosity,
                        default=logging.INFO,
                        dest='verbosity',
                        help='verbosity level')
    cfg_default = '/etc/transipddnsclient/config.ini'
    parser.add_argument('-c', '--config',
                        metavar='CFG',
                        default=cfg_default,
                        type=argparse.FileType('r'),
                        help=f'the configuration file (Default: {cfg_default})')
    parser.add_argument('-i', '--interface',
                        type=str,
                        help='use the specified interface IP address as source. '
                             'When not specified, the public IP address will be retrieved from the internet')
    args = parser.parse_args()

    # Set logging
    logging.basicConfig(level=args.verbosity, stream=sys.stdout)

    # Read config file
    config = configparser.ConfigParser()
    with args.config as f_config:
        config.read_file(f_config)

    # Retrieve main section
    cfg = config.pop('transipapi')

    # Create API instance
    api = TransIPApi(**cfg)

    # Determine the external IP source
    if args.interface is not None:
        ext_ip = WanIPSource(args.interface)
    else:
        ext_ip = RoundRobinRequestsIPSource()

    # Retrieve dns sections
    dns = [
        {
            'name': section,
            'expire': 0,
            'type': config[section].get('type'),
            'content': config[section].get('content'),
        }
        for section in config.sections()
    ]

    # Execute the transipddnsclient core functionality
    return transipddnsclient(api, ext_ip, dns)


if __name__ == '__main__':
    exit(transipddnsclient_main())
