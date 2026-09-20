"""A scripted HTTP opener for tests. Map URL → (status, headers, body) or a
callable returning that. A key ending in "*" matches any URL with that
prefix (SPARQL requests carry a long query string). Records every request."""
import io
from urllib.error import URLError


class FakeOpener:
    def __init__(self, routes: dict):
        self.routes = routes
        self.requests: list = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        url = request.full_url
        r = self.routes.get(url)
        if r is None:
            r = next((v for k, v in self.routes.items() if k.endswith("*") and url.startswith(k[:-1])), None)
        if r is None:
            raise URLError(f"no route for {url}")
        if callable(r):
            r = r(request)
        status, headers, body = r
        if isinstance(body, str):
            body = body.encode()
        return status, headers, io.BytesIO(body)
