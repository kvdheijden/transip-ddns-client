from ddns.core import ddns_main
from ddns import __version__
import ddns.provider

import argparse
import json
import logging
import sys

from typing import Sequence, Text


def load_provider(parser: argparse.ArgumentParser, arg: str) -> type:
    import importlib
    try:
        parts = arg.split('.')
        try:
            module = importlib.import_module('.'.join(parts[:-1]))
            provider = module.__getattribute__(parts[-1])
        except ImportError:
            module = importlib.import_module(parts[0])
            for i in range(1, len(parts)):
                module = module.__getattribute__(parts[i])
            provider = module

        if not issubclass(provider, ddns.provider.DDNSProvider):
            parser.error('The specified ddns provider must be an instance of ddns.provider.DDNSProvider')
        else:
            return provider
    except ImportError:
        parser.error(f'Could not load ddns provider "{arg}"')


class Verbosity(argparse.Action):
    def __init__(self, option_strings: Sequence[Text], dest: Text, nargs=None, const=None, default=None, type=None,
                 choices=None, required=False, help=None, metavar=None):
        super().__init__(option_strings, dest, nargs, const, default, type, choices, required, help, metavar)
        self.initial = logging.CRITICAL
        self.v = self.initial
        self._gain = 10

    def __call__(self, parser, args, values, option_string=None):
        if values is None:
            # -v -v -v -v -v
            self.v -= self._gain
        else:
            try:
                # -v 5
                self.v = self.initial - int(values) * self._gain
            except ValueError:
                # -vvvvv
                self.v = self.initial - (values.count('v') + 1) * self._gain

        if logging.NOTSET > self.v or self.v > logging.CRITICAL:
            parser.error('Verbosity level must be between 0 and 5.')

        setattr(args, self.dest, self.v)


def run_ddns() -> int:
    # Parse arguments
    parser = argparse.ArgumentParser('python -m ddns', description='Dynamic DNS Client')
    parser.add_argument('--version',
                        action='version',
                        version=__version__)
    parser.add_argument('-v',
                        nargs='?',
                        action=Verbosity,
                        default=logging.INFO,
                        dest='verbosity',
                        help='verbosity level')
    parser.add_argument('domain',
                        help='the domain name for which DNS entries need to be handled')
    parser.add_argument('dnsfile',
                        type=argparse.FileType('r'),
                        help='the file containing json encoded DNS entries')
    parser.add_argument('provider',
                        type=lambda arg: load_provider(parser, arg),
                        help='the dDNS provider used for updating DNS entries')
    parser.add_argument('arguments',
                        nargs='*',
                        default=[],
                        help='arguments for the specified dDNS provider')
    args = parser.parse_args()

    logging.basicConfig(level=args.verbosity, stream=sys.stdout)

    # Load the JSON DNS data and close the file
    with args.dnsfile as f:
        json_dns = f.read()
        dns = json.loads(json_dns)

    # Create a ddns provider using specified arguments
    provider_args = []
    provider_kwargs = {}
    for argument in args.arguments:
        if '=' in argument:
            k, v = tuple(argument.split('=', 1))
            provider_kwargs[k] = v
        else:
            provider_args.append(argument)

    try:
        provider = args.provider(*provider_args, **provider_kwargs)
    except TypeError:
        parser.error('Failed to create ddns provider with specified arguments')
        return 0

    # Execute the ddns core functionality
    ddns_main(args.domain, dns, provider)
    return 0


if __name__ == '__main__':
    exit(run_ddns())
