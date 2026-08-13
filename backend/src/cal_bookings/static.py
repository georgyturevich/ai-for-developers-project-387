"""Opt-in static SPA serving behind the STATIC_DIR env var (ticket #18).

When STATIC_DIR is set, the built frontend is served from that directory at
``/`` and unknown non-API GET paths fall back to ``index.html`` so deep UI
links survive refresh and sharing. Unknown API paths keep the contract's JSON
error body: paths under the API route namespace are never served statics.

Unset, the module contributes nothing — the app stays a pure API.
"""

from __future__ import annotations

from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

#: First path segments that belong to the API, not to the SPA. The contract
#: routes live under /event-types and /bookings; /api is reserved by convention
#: for future API namespaces so a bogus path there never gets SPA'd.
_API_SEGMENTS = ("event-types", "bookings", "api")


class SPAStaticFiles(StaticFiles):
    """StaticFiles that serves ``index.html`` for unknown non-API GET paths."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or _is_api_path(scope["path"]):
                raise
            return await super().get_response("index.html", scope)


def _is_api_path(path: str) -> bool:
    return path.strip("/").split("/", 1)[0] in _API_SEGMENTS
