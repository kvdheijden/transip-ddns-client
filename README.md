# dDNS

dDNS is a pluggable program which updates DNS entries whenever your public IP address changes.
Any provider which exposes an API can be used as dynamic DNS provider.
Current available DNS providers are:
 - TransIP

## Usage
```
usage: python -m ddns [-h] [--version] [-v [VERBOSITY]]
                      domain dnsfile provider [arguments [arguments ...]]

Dynamic DNS Client

positional arguments:
  domain          the domain name for which DNS entries need to be handled
  dnsfile         the file containing json encoded DNS entries
  provider        the ddns provider used for updating DNS entries
  arguments       arguments for the specified ddns provider

optional arguments:
  -h, --help      show this help message and exit
  --version       show program's version number and exit
  -v [VERBOSITY]  verbosity level
```

## Extending
Implementing a custom DNS provider is pretty straightforward: Create a subclass of the `ddns.provider.DDNSProvider`
class and implement the `update(self, current_ip: AnyStr, new_ip: AnyStr, domain: AnyStr, dns: List[Dict]) -> None`
method.
The implementation of the [TransIPProvider](ddns/provider/transip.py#TransIPProvider) can be used as an example
implementation.

## License
See the [LICENSE](LICENSE.md) file for license right and limitations (MIT)