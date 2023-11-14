from starlette.websockets import WebSocket
from starlette.exceptions import WebSocketException
from starlette.endpoints import WebSocketEndpoint, HTTPEndpoint
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
import random
import asyncio
import logging
logger = logging.getLogger(__name__)


index_str = """<!DOCTYPE HTML>
<html>
<head>
    <script type = "text/javascript">
    const websocket = new WebSocket("ws://localhost:8080/ws");
    window.addEventListener("DOMContentLoaded", () => {
        websocket.onmessage = ({ data }) => {
            console.log('Received: ' + data)
            document.body.innerHTML += data + "<br>";
        };
    });
    </script>
</head>
<body>
    WebSocket Async Experiment<br>
    <button onclick="websocket.send(Math.floor(Math.random()*10))">Send</button><br>
    <button onclick="websocket.send('ping')">Ping</button><br>
    <button onclick="websocket.send('get')">Get</button><br>
    <button onclick="websocket.send('update')">Update</button><br>
    <button onclick="websocket.send('close')">Close</button><br>
</body>
</html>
"""

class Homepage(HTTPEndpoint):
    async def get(self, request):
        return HTMLResponse(index_str)

# clients = []
class Consumer(WebSocketEndpoint):
    to_update = 'text'
    task = None
    clients = set()

    async def on_connect(self, websocket: WebSocket):
        logger.info(f"connection started {websocket.client.port}")
        await websocket.accept()
        self.clients.add(websocket)

    def broadcast(self, message):
        for client in self.clients:
            try:
                asyncio.create_task(client.send_text(message))
            except WebSocketException:
                # in case that a client closed while something was being broadcasted.
                pass

    async def on_receive(self, websocket: WebSocket, data: str):
        match data:
            case 'ping':
                if self.task is not None:
                    await websocket.send_text('background task is already running')
                    return

                await websocket.send_text('start background task')
                self.task = asyncio.create_task(self.simulate_long_task(websocket))
            case 'get':
                await websocket.send_text(str(self.to_update))
            case 'update':
                self.to_update = random.random()
                self.broadcast(f'updated to {self.to_update}')
            case 'close':
                await websocket.send_text('closing connection')
                await websocket.close()
            case _:
                self.broadcast(f'Server received {data} from client')


    async def simulate_long_task(self, websocket: WebSocket):
        await websocket.send_text('start long process')
        await asyncio.sleep(5)
        await websocket.send_text('finish long process')
        self.task = None

    async def on_disconnect(self, websocket, close_code):
        logger.info(f"connection closed {websocket.client_state} {close_code}")
        self.clients.remove(websocket)
        pass

routes = [
    Route("/", Homepage),
    WebSocketRoute("/ws", Consumer)
]