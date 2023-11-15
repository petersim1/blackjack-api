from starlette.endpoints import HTTPEndpoint
from starlette.responses import HTMLResponse

index_str = """<!DOCTYPE HTML>
<html>
<head>
    <script type = "text/javascript">
    const websocket = new WebSocket("ws://localhost:8080/ws");
    window.addEventListener("DOMContentLoaded", () => {
        websocket.onmessage = ({data}) => {
            console.log('Received: ' + data);
            const {count, text, policy} = JSON.parse(data);
            document.getElementById("count").innerHTML = count
            document.body.innerHTML += text + "<br>";
            Array.from(document.querySelectorAll("button[name]")).forEach((el) => {
                if (!policy.includes(el.name)) {
                    el.disabled = true
                } else {
                    el.disabled = false
                }
            });
        };
    });
    </script>
</head>
<body>
    WebSocket Async Experiment
    <div style="margin-bottom: 10px;">
        <button onclick="websocket.send('start_game')">Start Game</button><br>
    </div>
    <div id="count">0</div>
    <div style="display: flex; flex-direction: row; gap: 10px;">
        <button onclick="websocket.send('stay')" name="stay">Stay</button><br>
        <button onclick="websocket.send('hit')" name="hit">Hit</button><br>
        <button onclick="websocket.send('double')" name="double">Double</button><br>
        <button onclick="websocket.send('close')">End</button><br>
        <button onclick="websocket.send('get')">Get</button><br>
    </div>
</body>
</html>
"""

class Homepage(HTTPEndpoint):
    async def get(self, request):
        return HTMLResponse(index_str)