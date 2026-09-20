import pytest

from compliance_register.mirror import http
from tests.fakehttp import FakeOpener

HTML = {"Content-Type": "text/html; charset=utf-8"}


def client(routes, **kw):
    return http.Http(user_agent="t/1", delay_seconds=0, opener=FakeOpener(routes), sleep=lambda s: None, **kw)


def test_get_ok():
    c = client({"https://a.test/x": (200, HTML, "<p>hi</p>")})
    r = c.get("https://a.test/x", allowed_hosts=["a.test"])
    assert r.status == 200 and r.body == b"<p>hi</p>" and r.url == "https://a.test/x"


def test_follows_same_host_redirect():
    c = client({
        "https://a.test/x": (301, {"Location": "https://a.test/y"}, ""),
        "https://a.test/y": (200, HTML, "ok"),
    })
    assert c.get("https://a.test/x", allowed_hosts=["a.test"]).url == "https://a.test/y"


def test_refuses_cross_host_redirect():
    c = client({"https://a.test/x": (301, {"Location": "https://evil.test/y"}, "")})
    with pytest.raises(http.HttpRefused):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


def test_refuses_scheme_downgrade():
    c = client({"https://a.test/x": (301, {"Location": "http://a.test/y"}, "")})
    with pytest.raises(http.HttpRefused):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


def test_refuses_over_budget():
    c = client({"https://a.test/x": (200, HTML, "x" * 100)}, max_bytes=50)
    with pytest.raises(http.HttpRefused):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


def test_retries_then_unreachable():
    calls = {"n": 0}
    def flaky(req):
        calls["n"] += 1
        return (503, {}, "")
    c = client({"https://a.test/x": flaky})
    with pytest.raises(http.HttpUnreachable):
        c.get("https://a.test/x", allowed_hosts=["a.test"])
    assert calls["n"] == 3


def test_robots_disallow_refuses():
    c = client({
        "https://a.test/robots.txt": (200, {}, "User-agent: *\nDisallow: /private\n"),
        "https://a.test/private/x": (200, HTML, "secret"),
    })
    with pytest.raises(http.HttpRefused):
        c.get("https://a.test/private/x", allowed_hosts=["a.test"])


def test_robots_has_no_bypass_switch():
    import inspect
    assert not [n for n in inspect.signature(http.Http).parameters if "robots" in n]


def test_robots_url_from_hostname_and_port_not_netloc():
    opener = FakeOpener({
        "https://a.test:8443/robots.txt": (200, {}, "User-agent: *\nDisallow: /private\n"),
        "https://user:pw@a.test:8443/private/x": (200, HTML, "secret"),
    })
    c = http.Http(user_agent="t/1", delay_seconds=0, opener=opener, sleep=lambda s: None)
    with pytest.raises(http.HttpRefused):
        c.get("https://user:pw@a.test:8443/private/x", allowed_hosts=["a.test"])
    assert opener.requests[0].full_url == "https://a.test:8443/robots.txt"


def test_delay_between_same_host_requests():
    slept = []
    c = http.Http(user_agent="t/1", delay_seconds=7, opener=FakeOpener({
        "https://a.test/robots.txt": (404, {}, ""),
        "https://a.test/1": (200, HTML, "1"), "https://a.test/2": (200, HTML, "2")}), sleep=slept.append)
    c.get("https://a.test/1", allowed_hosts=["a.test"]); c.get("https://a.test/2", allowed_hosts=["a.test"])
    assert slept and slept[-1] == 7


def test_user_agent_strings():
    assert http.user_agent("neutral").startswith("curl/")
    assert "Firefox" in http.user_agent("browser")
    from compliance_register import __version__
    assert http.user_agent("default") == (
        f"compliance-register/{__version__} (+https://github.com/AlexSendula/compliance-register; contact: github@alexsendula.com)")


@pytest.mark.parametrize("loc", ["https://a.test/y\r\nX-Injected: 1", "https://a.test/y\x00", "https://[::1"])
def test_hostile_location_is_refused_not_raised(loc):
    c = client({"https://a.test/x": (301, {"Location": loc}, "")})
    with pytest.raises(http.HttpRefused):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


def test_server_side_http_exception_is_unreachable():
    import http.client as hc
    def broken(req):
        raise hc.IncompleteRead(b"partial")
    c = client({"https://a.test/x": broken})
    with pytest.raises(http.HttpUnreachable):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


def test_politeness_clock_is_shared_across_clients():
    """20 sources on one host = 20 clients; the delay must still apply between them."""
    http._LAST_BY_HOST.clear()
    routes = {"https://a.test/robots.txt": (404, {}, ""), "https://a.test/1": (200, HTML, "1"), "https://a.test/2": (200, HTML, "2")}
    slept = []
    a = http.Http(user_agent="t/1", delay_seconds=5, opener=FakeOpener(routes), sleep=slept.append)
    b = http.Http(user_agent="t/1", delay_seconds=5, opener=FakeOpener(routes), sleep=slept.append)
    a.get("https://a.test/1", allowed_hosts=["a.test"])
    assert slept == []
    b.get("https://a.test/2", allowed_hosts=["a.test"])
    assert slept == [5]


def test_per_call_max_bytes_overrides_client_budget():
    c = client({"https://a.test/x": (200, HTML, "x" * 100)}, max_bytes=1000)
    with pytest.raises(http.HttpRefused):
        c.get("https://a.test/x", allowed_hosts=["a.test"], max_bytes=50)
    assert c.get("https://a.test/x", allowed_hosts=["a.test"]).status == 200
