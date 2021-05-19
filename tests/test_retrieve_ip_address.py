def test_get_external_ip():
    from ddns.core import num_ip_sources, get_external_ip
    ip = None
    for i in range(num_ip_sources):
        if ip is None:
            ip = get_external_ip(i)
        else:
            assert ip == get_external_ip(i)
