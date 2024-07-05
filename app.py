import os
import socketio
from flask import Flask
from typing import Dict, Any

app = Flask(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST") or "localhost"
REDIS_PORT = os.environ.get("REDIS_PORT") or 6379
REDIS_DB = os.environ.get("REDIS_DB") or 0
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD") or None
REDIS_PROTOCOL = os.environ.get("REDIS_PROTOCOL") or "redis"

if REDIS_PASSWORD:
    REDIS_URI = f"{REDIS_PROTOCOL}://default:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    REDIS_URI = f"{REDIS_PROTOCOL}://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

mgr = socketio.RedisManager(REDIS_URI)
sio = socketio.Server(client_manager=mgr, cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)


@sio.event
def connect(sid: str, environ: Dict[str, Any]):
    print("connect ", sid)


active_players: Dict[str, Dict[str, str]] = {}


@sio.on("player_joined")
def player_joined(sid: str, data: Dict[str, str]):
    player_id: str = data.get("player_id")
    # 檢查是否有相同的 player_id
    for existing_sid, player_data in active_players.items():
        if player_data["player_id"] == player_id:
            # 如果找到相同的 player_id，斷開舊連接
            sio.disconnect(existing_sid)
            break
    active_players[sid] = {"player_id": player_id}
    sio.enter_room(sid, player_id)
    sio.emit("player_joined", {"player_id": player_id}, room=player_id)
    print(f"Player joined: {player_id}")
    print(f"Active players: {active_players}")


@sio.event
def disconnect(sid: str):
    if sid in active_players:
        player_id = active_players[sid]["player_id"]
        del active_players[sid]
        sio.leave_room(sid, player_id)
        sio.emit("player_left", {"player_id": player_id}, room=player_id)
        print(f"Player left: {player_id}")
        print(f"Active players: {active_players}")
    else:
        print(f"Unknown client disconnected: {sid}")


if __name__ == "__main__":
    socketio.run(app, debug=True)
