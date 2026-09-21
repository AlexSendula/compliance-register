import pytest

from compliance_register.mirror import http
from tests.fakehttp import FakeOpener

HTML = {"Content-Type": "text/html; charset=utf-8"}


def client(routes, **kw):
    # a host with no robots.txt (404) unless the test says otherwise — an unroutable
    # robots.txt is now "rules unknown", which is unreachable, not "no rules"
    routes = {"https://a.test/robots.txt": (404, {}, ""), **routes}
    kw.setdefault("user_agent", "t/1")
    return http.Http(delay_seconds=0, opener=FakeOpener(routes), sleep=lambda s: None, **kw)


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


def test_http_redirect_is_upgraded_to_https_and_never_requested_in_the_clear():
    """CELLAR's 303 points at http://publications.europa.eu/...; the same URL serves
    over https. Upgrade the scheme rather than refuse — and never send the http one."""
    c = client({"https://a.test/x": (301, {"Location": "http://a.test/y"}, ""), "https://a.test/y": (200, HTML, "ok")})
    assert c.get("https://a.test/x", allowed_hosts=["a.test"]).url == "https://a.test/y"
    assert all(r.full_url.startswith("https://") for r in c.opener.requests)


def test_extra_request_headers_are_sent():
    c = client({"https://a.test/x": (200, HTML, "ok")})
    c.get("https://a.test/x", allowed_hosts=["a.test"], headers={"Accept": "application/xhtml+xml", "Accept-Language": "nl"})
    req = [r for r in c.opener.requests if r.full_url == "https://a.test/x"][0]
    assert req.get_header("Accept") == "application/xhtml+xml" and req.get_header("Accept-language") == "nl"


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
    assert slept == [5]  # robots.txt set the clock, the page waited
    b.get("https://a.test/2", allowed_hosts=["a.test"])
    assert slept == [5, 5, 5]  # b's very first request (its robots.txt) waited on a's clock


def test_per_call_max_bytes_overrides_client_budget():
    c = client({"https://a.test/x": (200, HTML, "x" * 100)}, max_bytes=1000)
    with pytest.raises(http.HttpRefused):
        c.get("https://a.test/x", allowed_hosts=["a.test"], max_bytes=50)
    assert c.get("https://a.test/x", allowed_hosts=["a.test"]).status == 200


# --- robots.txt is read the way RFC 9309 says, and against our own name (P8) ---

def test_robots_redirect_is_followed_and_rules_applied():
    c = client({
        "https://a.test/robots.txt": (301, {"Location": "https://a.test/r/robots.txt"}, ""),
        "https://a.test/r/robots.txt": (200, {}, "User-agent: *\nDisallow: /private\n"),
        "https://a.test/private/x": (200, HTML, "secret"),
    })
    with pytest.raises(http.HttpRefused, match="robots"):
        c.get("https://a.test/private/x", allowed_hosts=["a.test"])


def test_robots_5xx_is_unreachable_not_fetched():
    c = client({"https://a.test/robots.txt": (503, {}, ""), "https://a.test/x": (200, HTML, "ok")})
    opener = c.opener
    with pytest.raises(http.HttpUnreachable, match="robots.txt"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])
    assert not [r for r in opener.requests if r.full_url == "https://a.test/x"]


def test_robots_4xx_means_no_rules():
    for status in (401, 403, 404, 410):
        c = client({"https://a.test/robots.txt": (status, {}, ""), "https://a.test/x": (200, HTML, "ok")})
        assert c.get("https://a.test/x", allowed_hosts=["a.test"]).status == 200


def test_robots_disallow_for_our_product_token_holds_under_browser_ua():
    routes = {
        "https://a.test/robots.txt": (200, {}, "User-agent: compliance-register\nDisallow: /\n"),
        "https://a.test/x": (200, HTML, "ok"),
    }
    for policy in ("default", "neutral", "browser"):
        c = http.Http(user_agent=http.user_agent(policy), delay_seconds=0, opener=FakeOpener(routes), sleep=lambda s: None)
        with pytest.raises(http.HttpRefused, match="robots"):
            c.get("https://a.test/x", allowed_hosts=["a.test"])


def test_plain_http_is_refused_even_when_a_listing_asks_for_it():
    """Legal text over plaintext can be altered on the path; the client speaks https only."""
    c = client({"http://a.test/x": (200, HTML, "ok")})
    with pytest.raises(http.HttpRefused, match="scheme"):
        c.get("http://a.test/x", allowed_hosts=["a.test"])


def test_robots_redirect_to_another_host_is_followed():
    """publications.europa.eu/robots.txt 301s to op.europa.eu/robots.txt. Rules can
    only restrict us, so the robots fetch may leave allowed_hosts — the page never can."""
    c = client({
        "https://a.test/robots.txt": (301, {"Location": "https://cdn.test/robots.txt"}, ""),
        "https://cdn.test/robots.txt": (200, {}, "User-agent: *\nDisallow: /private\n"),
        "https://a.test/private/x": (200, HTML, "secret"),
        "https://a.test/x": (200, HTML, "ok"),
    })
    with pytest.raises(http.HttpRefused, match="robots"):
        c.get("https://a.test/private/x", allowed_hosts=["a.test"])
    assert c.get("https://a.test/x", allowed_hosts=["a.test"]).status == 200
    assert not [r for r in c.opener.requests if "cdn.test" in r.full_url and not r.full_url.endswith("robots.txt")]


def test_robots_redirect_to_a_private_host_is_refused():
    c = client({"https://a.test/robots.txt": (301, {"Location": "https://127.0.0.1/robots.txt"}, ""), "https://a.test/x": (200, HTML, "ok")})
    with pytest.raises(http.HttpUnreachable, match="robots.txt"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])
    assert not [r for r in c.opener.requests if "127.0.0.1" in r.full_url]


# --- RFC 9309 matching: longest match wins, allow wins a tie, * and $ patterns ---

AP_STYLE = "User-agent: *\nDisallow: /admin/\nDisallow: /documenten\nAllow: /documenten/*\nDisallow: /vraag$\n\nUser-agent: GPTBot\nDisallow: /\n"


@pytest.mark.parametrize("path, allowed", [
    ("/documenten/handreiking-scraping", True),   # Allow /documenten/* (12) beats Disallow /documenten (11)
    ("/documenten", False),                        # only the Disallow matches
    ("/admin/x", False),
    ("/vraag", False),                             # $ anchors the end
    ("/vraag-van-de-maand", True),                 # ... so this does not match /vraag$
    ("/themas/x", True),
])
def test_robots_longest_match_and_allow_on_tie(path, allowed):
    c = client({"https://a.test/robots.txt": (200, {}, AP_STYLE), "https://a.test" + path: (200, HTML, "ok")})
    if allowed:
        assert c.get("https://a.test" + path, allowed_hosts=["a.test"]).status == 200
    else:
        with pytest.raises(http.HttpRefused, match="robots"):
            c.get("https://a.test" + path, allowed_hosts=["a.test"])


def test_robots_group_for_our_token_takes_precedence_over_star():
    """Under the default policy the presented UA is our token, so its group decides."""
    txt = "User-agent: *\nDisallow: /\n\nUser-agent: compliance-register\nAllow: /\n"
    c = client({"https://a.test/robots.txt": (200, {}, txt), "https://a.test/x": (200, HTML, "ok")}, user_agent=http.user_agent("default"))
    assert c.get("https://a.test/x", allowed_hosts=["a.test"]).status == 200
    txt2 = "User-agent: *\nAllow: /\n\nUser-agent: Compliance-Register\nDisallow: /\n"
    c = client({"https://a.test/robots.txt": (200, {}, txt2), "https://a.test/x": (200, HTML, "ok")}, user_agent=http.user_agent("default"))
    with pytest.raises(http.HttpRefused, match="robots"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


# --- SEC-003: the name a human confirmed must not resolve to a private address ---

def _client_with_resolver(routes, resolver):
    routes = {"https://a.test/robots.txt": (404, {}, ""), **routes}
    return http.Http(user_agent="t/1", delay_seconds=0, opener=FakeOpener(routes), sleep=lambda s: None, resolver=resolver)


def test_host_resolving_to_a_private_address_is_refused_before_any_request():
    c = _client_with_resolver({"https://a.test/x": (200, HTML, "ok")}, lambda host: ["127.0.0.1"])
    with pytest.raises(http.HttpRefused, match="resolves to a private"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])
    assert c.opener.requests == []


@pytest.mark.parametrize("addrs", [["8.8.8.8", "10.0.0.7"], ["fe80::1"], ["169.254.169.254"], ["::1"], ["0.0.0.0"], ["100.64.0.1"], ["::ffff:127.0.0.1"], ["224.0.0.1"], ["192.0.0.8"]])
def test_any_private_address_among_the_answers_refuses(addrs):
    c = _client_with_resolver({"https://a.test/x": (200, HTML, "ok")}, lambda host: addrs)
    with pytest.raises(http.HttpRefused, match="private"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


def test_unresolvable_host_is_unreachable_not_refused():
    import socket
    def boom(host):
        raise socket.gaierror(8, "nodename nor servname provided")
    c = _client_with_resolver({"https://a.test/x": (200, HTML, "ok")}, boom)
    with pytest.raises(http.HttpUnreachable, match="cannot resolve"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


def test_every_hop_is_resolved_including_a_robots_redirect_target():
    seen = []
    def resolver(host):
        seen.append(host)
        return ["10.1.1.1"] if host == "cdn.test" else ["8.8.8.8"]
    c = _client_with_resolver({
        "https://a.test/robots.txt": (301, {"Location": "https://cdn.test/robots.txt"}, ""),
        "https://a.test/x": (200, HTML, "ok"),
    }, resolver)
    with pytest.raises(http.HttpUnreachable, match="robots.txt"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])
    assert "cdn.test" in seen and not [r for r in c.opener.requests if "cdn.test" in r.full_url]


def test_default_resolver_is_the_os_resolver_and_returns_literals(monkeypatch):
    monkeypatch.undo()  # drop conftest's no-DNS stub: this is the one test that resolves a real name
    assert http.Http.__init__.__kwdefaults__["resolver"] is None
    addrs = http.resolve("localhost")  # the OS answers 127.0.0.1 and/or ::1 without any network
    assert addrs and all(http.is_private_host(a) for a in addrs)


def test_a_name_that_is_not_valid_idna_is_unreachable_not_a_traceback():
    """socket.getaddrinfo raises UnicodeError (a ValueError) for a 64-char label; that
    used to be caught inside _once and must still surface as unreachable, by name."""
    def real_like(host):
        if len(host.split(".")[0]) > 63:
            raise UnicodeError("label empty or too long")
        return ["8.8.8.8"]
    c = _client_with_resolver({"https://a.test/robots.txt": (301, {"Location": "https://" + "x" * 64 + ".test/robots.txt"}, "")}, real_like)
    with pytest.raises(http.HttpUnreachable, match="robots.txt unreadable"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


def test_transient_dns_failure_is_retried_with_backoff_then_unreachable():
    import socket
    calls, slept = [], []
    def flaky(host):
        calls.append(host)
        raise socket.gaierror(-3, "Temporary failure in name resolution")
    c = http.Http(user_agent="t/1", delay_seconds=0, opener=FakeOpener({"https://a.test/robots.txt": (404, {}, "")}), sleep=slept.append, resolver=flaky)
    with pytest.raises(http.HttpUnreachable, match="cannot resolve"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])
    assert len(calls) == http.RETRIES + 1 and slept == list(http.BACKOFF)
    assert c.opener.requests == []


# --- redirect budget, hostile scheme, retry set, header case ---

def test_more_than_max_hops_redirects_raises_http_refused():
    chain = lambda n: {f"https://a.test/{i}": (302, {"Location": f"https://a.test/{i + 1}"}, "") for i in range(n)}
    ok = client({**chain(http.MAX_HOPS), f"https://a.test/{http.MAX_HOPS}": (200, HTML, "ok")})
    assert ok.get("https://a.test/0", allowed_hosts=["a.test"]).url == f"https://a.test/{http.MAX_HOPS}"
    with pytest.raises(http.HttpRefused, match="redirects"):
        client(chain(http.MAX_HOPS + 1)).get("https://a.test/0", allowed_hosts=["a.test"])


def test_a_redirect_without_a_location_header_raises_http_refused():
    c = client({"https://a.test/x": (302, {}, "")})
    with pytest.raises(http.HttpRefused, match="without Location"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://a.test/x"])
def test_a_non_http_scheme_raises_http_refused_before_any_request(url):
    c = client({})
    with pytest.raises(http.HttpRefused, match="scheme"):
        c.get(url, allowed_hosts=["a.test"])
    assert c.opener.requests == []


def test_a_429_is_retried_like_a_5xx():
    calls = {"n": 0}
    def throttled(req):
        calls["n"] += 1
        return (429, {}, "")
    c = client({"https://a.test/x": throttled})
    with pytest.raises(http.HttpUnreachable, match="429"):
        c.get("https://a.test/x", allowed_hosts=["a.test"])
    assert calls["n"] == http.RETRIES + 1


def test_response_header_keys_are_title_cased():
    c = client({"https://a.test/x": (200, {"content-type": "text/html", "X-CUSTOM": "1"}, "ok")})
    r = c.get("https://a.test/x", allowed_hosts=["a.test"])
    assert r.headers["Content-Type"] == "text/html" and r.headers["X-Custom"] == "1" and "content-type" not in r.headers
