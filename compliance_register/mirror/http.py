"""HTTP with the safety docs-mirror learned the hard way: every redirect hop
is judged before it is taken, https never downgrades, bodies are read under a
budget, transient failures are retried a little and then reported as
unreachable — never as 'no change'. robots.txt is always honoured, per host;
there is no allowlist (D24)."""
from __future__ import annotations

import http.client
import ipaddress
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

from .. import __version__

MAX_HOPS = 5
RETRIES = 2
BACKOFF = (2, 6)
# what http.client itself refuses in a request target; catching it here keeps a
# hostile Location a refusal instead of an InvalidURL traceback
_CONTROL = re.compile(r"[\x00-\x20\x7f]")
# one clock per host for the whole process: check/fetch build one client per
# source, and twenty sources on one host must still wait between requests
_LAST_BY_HOST: dict[str, float] = {}

_UA = {
    "default": f"compliance-register/{__version__} (+https://github.com/AlexSendula/compliance-register; contact: github@alexsendula.com)",
    "neutral": "curl/8.0",
    "browser": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
}


def user_agent(policy: str) -> str:
    return _UA.get(policy, _UA["default"])


class HttpRefused(Exception):
    """We chose not to fetch: policy, robots, budget, content."""


class HttpUnreachable(Exception):
    """We tried and could not: network, timeout, server error."""


@dataclass
class Response:
    status: int
    headers: dict
    body: bytes
    url: str


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _default_opener(request, timeout):
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        resp = opener.open(request, timeout=timeout)
        return resp.status, dict(resp.headers), resp
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e


def is_private_host(host: str) -> bool:
    """A literal address we never fetch: anything that is not globally routable
    (loopback, RFC 1918, link-local, CGNAT 100.64/10, IPv4-mapped, reserved,
    documentation, unspecified), multicast, or the name localhost. A name is
    checked by what it resolves to — see _refuse_private_resolution (SEC-003)."""
    if host.lower() == "localhost":
        return True
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return False
    return not ip.is_global or ip.is_multicast or bool(getattr(ip, "is_site_local", False))


def resolve(host: str) -> list[str]:
    """Every address the OS resolver answers for host, v4 and v6, as literals.
    Raises OSError (socket.gaierror) when the name does not resolve."""
    infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    return sorted({str(info[4][0]) for info in infos})


def _product_token(user_agent: str) -> str:
    return user_agent.split("/", 1)[0].strip().lower()


class _Robots:
    """robots.txt per RFC 9309 §2.2: groups by product token (case-insensitive,
    merged, `*` as fallback), rules with `*` and a trailing `$`, the longest
    matching pattern wins and an allow wins a tie. urllib.robotparser takes the
    first matching rule instead, which turns `Disallow: /documenten` +
    `Allow: /documenten/*` into a refusal of every document."""

    def __init__(self, text: str):
        self.groups: dict[str, list[tuple[bool, str]]] = {}
        agents: list[str] = []
        collecting = False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            field, _, value = line.partition(":")
            field, value = field.strip().lower(), value.strip()
            if field == "user-agent":
                if collecting:  # a User-agent after rules starts a new group
                    agents, collecting = [], False
                agents.append(_product_token(value))
            elif field in ("allow", "disallow") and agents:
                collecting = True
                if value:  # an empty Disallow means "nothing is disallowed" and adds no rule
                    for a in agents:
                        self.groups.setdefault(a, []).append((field == "allow", value))

    @staticmethod
    def _matches(pattern: str, path: str) -> bool:
        rx = "^" + re.escape(pattern).replace(r"\*", ".*")
        if rx.endswith(r"\$"):
            rx = rx[:-2] + "$"
        return re.match(rx, path) is not None

    def allowed(self, user_agent: str, path: str) -> bool:
        rules = self.groups.get(_product_token(user_agent))
        if rules is None:
            rules = self.groups.get("*")
        if not rules:
            return True
        best: tuple[int, bool] | None = None
        for allow, pattern in rules:
            if self._matches(pattern, path):
                key = (len(pattern), allow)  # longest wins; on equal length True (allow) sorts last
                if best is None or key > best:
                    best = key
        return True if best is None else best[1]


class Http:
    def __init__(self, *, user_agent: str, delay_seconds: int = 10, timeout: int = 30,
                 max_bytes: int = 20_000_000, opener=None, sleep=time.sleep, resolver=None):
        self.ua = user_agent
        self.resolver = resolver  # None: the module's resolve(), looked up at call time
        self.delay = delay_seconds
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.opener = opener or _default_opener
        self.sleep = sleep
        # per host: parsed rules, None (no robots.txt), or the error that made the rules unknowable
        self._robots: dict[str, _Robots | HttpUnreachable | None] = {}

    # --- politeness ---------------------------------------------------
    def _wait(self, host: str) -> None:
        last = _LAST_BY_HOST.get(host)
        if last is not None and self.delay:
            self.sleep(self.delay)
        _LAST_BY_HOST[host] = time.monotonic()

    # --- robots -------------------------------------------------------
    def _allowed_by_robots(self, url: str) -> bool:
        """RFC 9309: follow redirects to the file — even to another host, since
        publications.europa.eu sends its robots.txt to op.europa.eu and rules can
        only ever restrict us; 4xx means no rules; 5xx or a network failure means
        the rules are unknown, so the host is unreachable for us — never fetched
        anyway. The rules are evaluated against our own product token as well as
        the User-Agent actually presented, so a site that names
        compliance-register is honoured under every UA policy."""
        parts = urlsplit(url)
        host = parts.hostname or ""
        if host not in self._robots:
            authority = f"{host}:{parts.port}" if parts.port else host
            robots_url = f"{parts.scheme}://{authority}/robots.txt"
            try:
                resp = self._follow(robots_url, allowed_hosts=None, budget=200_000, robots=False)
            except (HttpRefused, HttpUnreachable) as exc:  # a refused redirect or budget leaves the rules just as unknown
                self._robots[host] = HttpUnreachable(f"robots.txt unreadable, rules unknown: {exc}")
            else:
                if 200 <= resp.status < 300:
                    self._robots[host] = _Robots(resp.body.decode("utf-8", "replace"))
                elif 400 <= resp.status < 500:
                    self._robots[host] = None
                else:
                    self._robots[host] = HttpUnreachable(f"robots.txt unreadable, rules unknown: {robots_url}: HTTP {resp.status}")
        rp = self._robots[host]
        if isinstance(rp, Exception):
            raise rp
        if rp is None:
            return True
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        return rp.allowed(_UA["default"], path) and rp.allowed(self.ua, path)

    def _refuse_private_resolution(self, url: str, host: str) -> None:
        """SEC-003: a public name a human confirmed may still resolve to a
        private address. Resolve it ourselves before every hop and refuse if any
        answer is private. A transient resolver failure gets the same few
        retries a 5xx gets; a name that cannot be resolved is unreachable.

        What remains is the window between this lookup and urllib's own
        (TTL-0 rebinding). It is not a practical bypass: the client is https-only
        with certificate verification, so a private target would have to present
        a certificate valid for the confirmed name before a byte of HTTP is sent.
        Pinning the connection to the vetted address would close it fully at the
        cost of a custom HTTPS connection class."""
        last_exc: Exception | None = None
        for attempt in range(RETRIES + 1):
            try:
                addrs = (self.resolver or resolve)(host)
                break
            except (OSError, ValueError) as exc:  # gaierror; UnicodeError for a bad IDNA label
                last_exc = exc
                if attempt < RETRIES:
                    self.sleep(BACKOFF[attempt])
        else:
            raise HttpUnreachable(f"{url}: cannot resolve {host}: {last_exc}")
        if not addrs:
            raise HttpUnreachable(f"{url}: cannot resolve {host}: no address")
        bad = [a for a in addrs if is_private_host(a)]
        if bad:
            raise HttpRefused(f"{url}: {host} resolves to a private or local address ({', '.join(bad)})")

    # --- one hop ------------------------------------------------------
    def _once(self, url: str, max_bytes: int, headers: dict[str, str] | None = None) -> tuple[int, dict, bytes]:
        hdrs = {"User-Agent": self.ua, "Accept": "text/html,application/xhtml+xml,application/xml,text/csv,*/*;q=0.5", **(headers or {})}
        req = urllib.request.Request(url, headers=hdrs)
        last_exc: Exception | None = None
        for attempt in range(RETRIES + 1):
            try:
                status, headers, reader = self.opener(req, self.timeout)
                if status in (429,) or 500 <= status < 600:
                    last_exc = HttpUnreachable(f"{url}: HTTP {status}")
                else:
                    body = reader.read(max_bytes + 1)
                    if len(body) > max_bytes:
                        raise HttpRefused(f"{url}: body exceeds {max_bytes} bytes")
                    return status, {k.title(): v for k, v in headers.items()}, body
            except (urllib.error.URLError, OSError, TimeoutError, http.client.HTTPException, ValueError) as exc:
                last_exc = HttpUnreachable(f"{url}: {exc}")
            if attempt < RETRIES:
                self.sleep(BACKOFF[attempt])
        raise last_exc or HttpUnreachable(url)

    # --- public -------------------------------------------------------
    def get(self, url: str, *, allowed_hosts: list[str], max_bytes: int | None = None,
            headers: dict[str, str] | None = None) -> Response:
        """max_bytes caps this call's body below the client budget (listings);
        headers adds or overrides request headers (Accept, Accept-Language)."""
        budget = self.max_bytes if max_bytes is None else min(max_bytes, self.max_bytes)
        return self._follow(url, allowed_hosts=allowed_hosts, budget=budget, robots=True, headers=headers)

    def _follow(self, url: str, *, allowed_hosts: list[str] | None, budget: int, robots: bool,
                headers: dict[str, str] | None = None) -> Response:
        """Every hop is judged before it is taken. allowed_hosts=None (robots.txt
        only) admits any public host; robots=False only for robots.txt itself."""
        current = url
        for _ in range(MAX_HOPS + 1):
            parts = urlsplit(current)
            if parts.scheme != "https":  # a listing or config may name http://; legal text is never read in the clear
                raise HttpRefused(f"{current}: scheme not allowed (https only)")
            if allowed_hosts is None:
                if not parts.hostname or is_private_host(parts.hostname):
                    raise HttpRefused(f"{current}: private or local host")
            elif parts.hostname not in allowed_hosts:
                raise HttpRefused(f"{current}: host {parts.hostname} not in allowed_hosts {allowed_hosts}")
            self._refuse_private_resolution(current, parts.hostname)
            if robots and not self._allowed_by_robots(current):
                raise HttpRefused(f"{current}: disallowed by robots.txt")
            self._wait(parts.hostname or "")
            status, resp_headers, body = self._once(current, budget, headers)
            if status in (301, 302, 303, 307, 308):
                loc = resp_headers.get("Location")
                if not loc:
                    raise HttpRefused(f"{current}: redirect without Location")
                if _CONTROL.search(loc):
                    raise HttpRefused(f"{current}: redirect target contains control characters")
                try:
                    nxt = urljoin(current, loc)
                    urlsplit(nxt)
                except ValueError as exc:
                    raise HttpRefused(f"{current}: unparseable redirect target: {exc}")
                if urlsplit(nxt).scheme == "http":
                    # CELLAR's 303 names http://; the same URL serves over https. Upgrade,
                    # never follow in the clear — the https-only check above then judges it.
                    nxt = "https://" + nxt[len("http://"):]
                current = nxt
                continue
            return Response(status=status, headers=resp_headers, body=body, url=current)
        raise HttpRefused(f"{url}: more than {MAX_HOPS} redirects")
