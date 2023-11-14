from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

async def index(request: Request):
    return JSONResponse("Hello World!")

routes = [
    Route("/", index, methods=["GET"])
]