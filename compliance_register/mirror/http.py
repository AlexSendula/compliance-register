"""HTTP with the safety docs-mirror learned the hard way: every redirect hop
is judged before it is taken, https never downgrades, bodies are read under a
budget, transient failures are retried a little and then reported as
unreachable — never as 'no change'. robots.txt is always honoured, per host;
there is no allowlist (D24)."""
from __future__ import annotations

import http.client
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
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


class Http:
    def __init__(self, *, user_agent: str, delay_seconds: int = 10, timeout: int = 30,
                 max_bytes: int = 20_000_000, opener=None, sleep=time.sleep):
        self.ua = user_agent
        self.delay = delay_seconds
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.opener = opener or _default_opener
        self.sleep = sleep
        # per host: parsed rules, None (no robots.txt), or the error that made the rules unknowable
        self._robots: dict[str, urllib.robotparser.RobotFileParser | HttpUnreachable | None] = {}

    # --- politeness ---------------------------------------------------
    def _wait(self, host: str) -> None:
        last = _LAST_BY_HOST.get(host)
        if last is not None and self.delay:
            self.sleep(self.delay)
        _LAST_BY_HOST[host] = time.monotonic()

    # --- robots -------------------------------------------------------
    def _allowed_by_robots(self, url: str, allowed_hosts: list[str]) -> bool:
        """RFC 9309: follow redirects to the file; 4xx means no rules; 5xx or a
        network failure means the rules are unknown, so the host is unreachable
        for us — never fetched anyway. The rules are evaluated against our own
        product token as well as the User-Agent actually presented, so a site
        that names compliance-register is honoured under every UA policy."""
        parts = urlsplit(url)
        host = parts.hostname or ""
        if host not in self._robots:
            authority = f"{host}:{parts.port}" if parts.port else host
            robots_url = f"{parts.scheme}://{authority}/robots.txt"
            try:
                resp = self._follow(robots_url, allowed_hosts=allowed_hosts, budget=200_000, robots=False)
            except (HttpRefused, HttpUnreachable) as exc:  # a refused redirect or budget leaves the rules just as unknown
                self._robots[host] = HttpUnreachable(f"robots.txt unreadable, rules unknown: {exc}")
            else:
                if 200 <= resp.status < 300:
                    rp = urllib.robotparser.RobotFileParser()
                    rp.parse(resp.body.decode("utf-8", "replace").splitlines())
                    self._robots[host] = rp
                elif 400 <= resp.status < 500:
                    self._robots[host] = None
                else:
                    self._robots[host] = HttpUnreachable(f"robots.txt unreadable, rules unknown: {robots_url}: HTTP {resp.status}")
        rp = self._robots[host]
        if isinstance(rp, Exception):
            raise rp
        if rp is None:
            return True
        return rp.can_fetch(_UA["default"], url) and rp.can_fetch(self.ua, url)

    # --- one hop ------------------------------------------------------
    def _once(self, url: str, max_bytes: int) -> tuple[int, dict, bytes]:
        req = urllib.request.Request(url, headers={"User-Agent": self.ua, "Accept": "text/html,application/xhtml+xml,application/xml,text/csv,*/*;q=0.5"})
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
    def get(self, url: str, *, allowed_hosts: list[str], max_bytes: int | None = None) -> Response:
        """max_bytes caps this call's body below the client budget (listings)."""
        budget = self.max_bytes if max_bytes is None else min(max_bytes, self.max_bytes)
        return self._follow(url, allowed_hosts=allowed_hosts, budget=budget, robots=True)

    def _follow(self, url: str, *, allowed_hosts: list[str], budget: int, robots: bool) -> Response:
        """Every hop is judged before it is taken; robots=False only for robots.txt itself."""
        current = url
        for _ in range(MAX_HOPS + 1):
            parts = urlsplit(current)
            if parts.scheme != "https":  # a listing or config may name http://; legal text is never read in the clear
                raise HttpRefused(f"{current}: scheme not allowed (https only)")
            if parts.hostname not in allowed_hosts:
                raise HttpRefused(f"{current}: host {parts.hostname} not in allowed_hosts {allowed_hosts}")
            if robots and not self._allowed_by_robots(current, allowed_hosts):
                raise HttpRefused(f"{current}: disallowed by robots.txt")
            self._wait(parts.hostname or "")
            status, headers, body = self._once(current, budget)
            if status in (301, 302, 303, 307, 308):
                loc = headers.get("Location")
                if not loc:
                    raise HttpRefused(f"{current}: redirect without Location")
                if _CONTROL.search(loc):
                    raise HttpRefused(f"{current}: redirect target contains control characters")
                try:
                    nxt = urljoin(current, loc)
                    urlsplit(nxt)
                except ValueError as exc:
                    raise HttpRefused(f"{current}: unparseable redirect target: {exc}")
                if urlsplit(current).scheme == "https" and urlsplit(nxt).scheme == "http":
                    raise HttpRefused(f"{current}: refuses https→http downgrade to {nxt}")
                current = nxt
                continue
            return Response(status=status, headers=headers, body=body, url=current)
        raise HttpRefused(f"{url}: more than {MAX_HOPS} redirects")
