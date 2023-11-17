from starlette.endpoints import HTTPEndpoint
from starlette.responses import HTMLResponse

index_str = """<!DOCTYPE HTML>
<html>
<head>
    <script type = "text/javascript">
    const websocket = new WebSocket("ws://localhost:8080/ws");
    window.addEventListener("DOMContentLoaded", () => {
        websocket.onmessage = ({data}) => {
            const {
                balance,
                count,
                true_count,
                text,
                policy,
                house_cards,
                player_cards,
                player_total,
            } = JSON.parse(data);
            document.getElementById("profit").innerHTML = balance
            document.getElementById("count").innerHTML = count
            document.getElementById("true-count").innerHTML = true_count.toFixed(4)
            if (!!text) {
                document.body.innerHTML += text + "<br>";
            }
            if (player_total > 0) {
                document.body.innerHTML += "House Cards: " + String(house_cards) + " --- ";
                document.body.innerHTML += "Player Cards: " + String(player_cards) + " --- ";
                document.body.innerHTML += String(player_total) + "<br>";
            }
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
        <button onclick="websocket.send(JSON.stringify({code: 'start'}))">Start Game</button><br>
    </div>
    <div>Profit: <span id="profit">0</span> units</div>
    <div>Count: <span id="count">0</span></div>
    <div>True Count: <span id="true-count">0</span></div>
    <div style="display: flex; flex-direction: row; gap: 10px;">
        <button onclick="websocket.send(JSON.stringify({code: 'step', move: 'stay'}))" name="stay">Stay</button><br>
        <button onclick="websocket.send(JSON.stringify({code: 'step', move: 'hit'}))" name="hit">Hit</button><br>
        <button onclick="websocket.send(JSON.stringify({code: 'step', move: 'double'}))" name="double">Double</button><br>
        <button onclick="websocket.send(JSON.stringify({code: 'close'}))">End</button><br>
    </div>
</body>
</html>
"""

class Homepage(HTTPEndpoint):
    async def get(self, request):
        return HTMLResponse(index_str)