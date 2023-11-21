from starlette.routing import WebSocketRoute

from .ws import Consumer

routes = [
    WebSocketRoute("/", Consumer)
]

__all__ = ["routes"]