from starlette.routing import Route, WebSocketRoute

from .http import Homepage
from .ws import Consumer

routes = [
    Route("/", Homepage),
    WebSocketRoute("/ws", Consumer)
]

__all__ = ["routes"]