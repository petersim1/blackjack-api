from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route, WebSocketRoute

from .ws import Consumer


class Test(HTTPEndpoint):
    async def get(self, request: Request):
        return PlainTextResponse("Hello world!")

routes = [
    Route("/", Test),
    WebSocketRoute("/ws", Consumer)
    ]

__all__ = ["routes"]
