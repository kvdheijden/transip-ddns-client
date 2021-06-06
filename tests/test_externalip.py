import pytest
from transipddnsclient.externalip import RoundRobinRequestsIPSource, WanIPSource


@pytest.fixture
def ip_source():
    return RoundRobinRequestsIPSource()


def test_get_by_source(ip_source):
    sources = ip_source.ip_sources
    result = {}

    for s in sources:
        try:
            result[s] = ip_source.get_by_source(sources[s])
        except Exception:
            result[s] = None

    assert len(set(result[k] for k in result)) == 1, 'Not all IP sources returned the same IP address:\n' \
                                                     + '\n'.join(f'{k}: {result[k]}' for k in result)
