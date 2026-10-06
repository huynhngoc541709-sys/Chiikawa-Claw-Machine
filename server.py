import os
import sys
import io
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
import random
import threading
from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "chiikawa-claw-secret-key-2026")
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=30,
    ping_interval=15
)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# In-memory rooms database
# rooms[room_id] = { ... }
rooms = {}
rooms_lock = threading.Lock()

# 20 Chiikawa plushies database
PLUSHIES = [
    {"id": "chiikawa", "name": "Chiikawa", "rarity": "THƯỜNG", "rate": 0.65, "color": "#FFF2F5", "badge": "🧸"},
    {"id": "hachiware", "name": "Hachiware", "rarity": "THƯỜNG", "rate": 0.65, "color": "#E3F2FD", "badge": "🐱"},
    {"id": "usagi", "name": "Usagi", "rarity": "THƯỜNG", "rate": 0.60, "color": "#FFF9C4", "badge": "🐰"},
    {"id": "kurimanju", "name": "Kurimanju", "rarity": "THƯỜNG", "rate": 0.60, "color": "#EFEBE9", "badge": "🌰"},
    {"id": "shisa", "name": "Shisa", "rarity": "THƯỜNG", "rate": 0.55, "color": "#FFF3E0", "badge": "🦁"},
    {"id": "armor_worker", "name": "Armor-san Lao Động", "rarity": "THƯỜNG", "rate": 0.55, "color": "#ECEFF1", "badge": "🛡️"},
    {"id": "armor_ramen", "name": "Armor-san Tiệm Mì", "rarity": "THƯỜNG", "rate": 0.55, "color": "#FFF8E1", "badge": "🍜"},
    {"id": "goblin", "name": "Goblin Xanh", "rarity": "THƯỜNG", "rate": 0.50, "color": "#E8F5E9", "badge": "👺"},
    
    {"id": "momonga", "name": "Momonga", "rarity": "HIẾM", "rate": 0.38, "color": "#F3E5F5", "badge": "🐿️"},
    {"id": "rakko", "name": "Rakko Thầy Kiếm Sĩ", "rarity": "HIẾM", "rate": 0.35, "color": "#E0F7FA", "badge": "🦦"},
    {"id": "pajama_chiikawa", "name": "Pajama Chiikawa", "rarity": "HIẾM", "rate": 0.35, "color": "#FCE4EC", "badge": "🎀"},
    {"id": "pajama_hachiware", "name": "Pajama Hachiware", "rarity": "HIẾM", "rate": 0.35, "color": "#E1F5FE", "badge": "💤"},
    {"id": "pajama_usagi", "name": "Pajama Usagi", "rarity": "HIẾM", "rate": 0.35, "color": "#FFFDE7", "badge": "⭐"},
    {"id": "chii_kabuto", "name": "Chii-Kabuto Bọ Nhỏ", "rarity": "HIẾM", "rate": 0.32, "color": "#EDE7F6", "badge": "🪲"},
    {"id": "star_hoshi", "name": "Hoshi Sao Băng", "rarity": "HIẾM", "rate": 0.30, "color": "#FFF9C4", "badge": "🌟"},
    {"id": "chiikawa_mage", "name": "Chiikawa Pháp Sư", "rarity": "HIẾM", "rate": 0.28, "color": "#F8BBD0", "badge": "🪄"},
    {"id": "beetle_leaf", "name": "Bọ Lá Xanh Bạn", "rarity": "HIẾM", "rate": 0.30, "color": "#DCEDC8", "badge": "🍃"},
    
    {"id": "legend_usagi", "name": "Usagi Chiến Thần Yahaha", "rarity": "HUYỀN THOẠI", "rate": 0.16, "color": "#FFE082", "badge": "⚡"},
    {"id": "legend_momonga", "name": "Momonga Nữ Hoàng Vương Miện", "rarity": "HUYỀN THOẠI", "rate": 0.14, "color": "#E1BEE7", "badge": "👑"},
    {"id": "legend_golden_chiikawa", "name": "Golden Chiikawa Thần Tài", "rarity": "HUYỀN THOẠI", "rate": 0.12, "color": "#FFD54F", "badge": "🏆"}
]

DISCONNECT_GRACE_PERIOD = 50.0  # seconds to keep disconnected player before kicking
TURN_TIME_LIMIT = 25.0          # seconds per turn
DISCONNECTED_TURN_TIME_LIMIT = 8.0 # if active player disconnects, switch turn faster

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/plushies")
def get_plushies():
    return jsonify(PLUSHIES)

def get_room_summary(room):
    return {
        "id": room["id"],
        "name": room["name"],
        "gameState": room["gameState"],
        "currentTurnPlayerId": room["currentTurnPlayerId"],
        "turnTimer": max(0, int(room["turnEndTime"] - time.time())) if room["turnEndTime"] else 0,
        "claw": room["claw"],
        "players": [
            {
                "id": p["id"],
                "name": p["name"],
                "connected": p["connected"],
                "coins": p["coins"],
                "isTurn": p["id"] == room["currentTurnPlayerId"]
            }
            for p in room["players"]
        ]
    }

def advance_turn(room_id):
    with rooms_lock:
        if room_id not in rooms:
            return
        room = rooms[room_id]
        connected_players = [p for p in room["players"] if p["connected"]]
        if not connected_players:
            room["currentTurnPlayerId"] = None
            room["gameState"] = "waiting"
            room["turnEndTime"] = 0
            return

        # Find next player index
        current_id = room["currentTurnPlayerId"]
        current_idx = -1
        for idx, p in enumerate(room["players"]):
            if p["id"] == current_id:
                current_idx = idx
                break

        # Move forward until a connected player is found
        next_player = None
        for step in range(1, len(room["players"]) + 1):
            target_idx = (current_idx + step) % len(room["players"])
            candidate = room["players"][target_idx]
            if candidate["connected"]:
                next_player = candidate
                break

        if next_player:
            room["currentTurnPlayerId"] = next_player["id"]
            room["gameState"] = "playing"
            room["turnEndTime"] = time.time() + TURN_TIME_LIMIT
            room["claw"] = {"x": 50.0, "state": "idle", "open": True}
        else:
            room["currentTurnPlayerId"] = None
            room["gameState"] = "waiting"
            room["turnEndTime"] = 0

    socketio.emit("room_state_update", get_room_summary(rooms[room_id]), room=room_id)

def background_tick_monitor():
    """Monitors turns and disconnected players in the background."""
    while True:
        time.sleep(1.0)
        now = time.time()
        rooms_to_delete = []

        with rooms_lock:
            for room_id, room in list(rooms.items()):
                # 1. Check disconnected players
                players_to_remove = []
                for p in room["players"]:
                    if not p["connected"] and p["disconnect_time"]:
                        if now - p["disconnect_time"] > DISCONNECT_GRACE_PERIOD:
                            players_to_remove.append(p)

                for p in players_to_remove:
                    room["players"].remove(p)
                    socketio.emit("player_left_permanently", {"playerId": p["id"], "name": p["name"]}, room=room_id)
                    # If this player had the turn, advance immediately
                    if room["currentTurnPlayerId"] == p["id"]:
                        advance_turn(room_id)

                if not room["players"]:
                    rooms_to_delete.append(room_id)
                    continue

                # 2. Check turn expiry
                if room["gameState"] == "playing" and room["turnEndTime"]:
                    current_p = next((p for p in room["players"] if p["id"] == room["currentTurnPlayerId"]), None)
                    if not current_p or not current_p["connected"]:
                        # Player disconnected while having the turn - expire quickly
                        if room.get("disconnectionTurnExpire") and now > room["disconnectionTurnExpire"]:
                            room["disconnectionTurnExpire"] = None
                            advance_turn(room_id)
                    elif now >= room["turnEndTime"]:
                        # Normal turn timeout
                        advance_turn(room_id)

            for rid in rooms_to_delete:
                del rooms[rid]

monitor_thread = threading.Thread(target=background_tick_monitor, daemon=True)
monitor_thread.start()

# --- Socket.IO Events ---

@socketio.on("connect")
def on_connect():
    pass

@socketio.on("create_room")
def on_create_room(data):
    player_id = data.get("playerId")
    player_name = data.get("playerName", "Người chơi Chiikawa")
    room_name = data.get("roomName") or f"Tiệm Gắp {random.randint(100, 999)}"
    room_id = f"CHII-{random.randint(1000, 9999)}"
    
    with rooms_lock:
        room = {
            "id": room_id,
            "name": room_name,
            "gameState": "playing",
            "currentTurnPlayerId": player_id,
            "turnEndTime": time.time() + TURN_TIME_LIMIT,
            "claw": {"x": 50.0, "state": "idle", "open": True},
            "players": [
                {
                    "id": player_id,
                    "name": player_name,
                    "socket_id": request.sid,
                    "connected": True,
                    "coins": data.get("coins", 10),
                    "disconnect_time": None
                }
            ]
        }
        rooms[room_id] = room

    join_room(room_id)
    emit("room_created", {"roomId": room_id, "room": get_room_summary(room)})

@socketio.on("join_room")
def on_join_room(data):
    room_id = data.get("roomId", "").strip().upper()
    player_id = data.get("playerId")
    player_name = data.get("playerName", "Khách gắp thú")

    with rooms_lock:
        if room_id not in rooms:
            emit("error_message", {"message": f"Không tìm thấy phòng {room_id}! Hãy kiểm tra lại mã phòng."})
            return
        
        room = rooms[room_id]
        # Check if player already in room (re-attaching socket)
        existing = next((p for p in room["players"] if p["id"] == player_id), None)
        if existing:
            existing["socket_id"] = request.sid
            existing["connected"] = True
            existing["disconnect_time"] = None
        else:
            room["players"].append({
                "id": player_id,
                "name": player_name,
                "socket_id": request.sid,
                "connected": True,
                "coins": data.get("coins", 10),
                "disconnect_time": None
            })
            if not room["currentTurnPlayerId"]:
                room["currentTurnPlayerId"] = player_id
                room["gameState"] = "playing"
                room["turnEndTime"] = time.time() + TURN_TIME_LIMIT

    join_room(room_id)
    emit("joined_room_success", {"roomId": room_id, "room": get_room_summary(room)})
    socketio.emit("room_state_update", get_room_summary(room), room=room_id)

@socketio.on("reconnect_player")
def on_reconnect_player(data):
    """Handles Section 23: Restoring room and game state after network drop."""
    room_id = data.get("roomId")
    player_id = data.get("playerId")
    player_name = data.get("playerName")

    with rooms_lock:
        if not room_id or room_id not in rooms:
            emit("reconnect_failed", {"message": "Phòng không tồn tại hoặc đã hết hạn."})
            return
        
        room = rooms[room_id]
        player = next((p for p in room["players"] if p["id"] == player_id), None)
        
        if not player:
            emit("reconnect_failed", {"message": "Người chơi không còn trong phòng này."})
            return
        
        # Recover player socket and connection status
        player["socket_id"] = request.sid
        player["connected"] = True
        player["disconnect_time"] = None
        if "disconnectionTurnExpire" in room:
            room["disconnectionTurnExpire"] = None

    join_room(room_id)
    summary = get_room_summary(room)
    emit("reconnected_success", {
        "room": summary,
        "player": player,
        "gameState": room["gameState"],
        "currentTurn": room["currentTurnPlayerId"],
        "claw": room["claw"],
        "players": summary["players"]
    })
    socketio.emit("room_state_update", summary, room=room_id)

@socketio.on("move_claw")
def on_move_claw(data):
    room_id = data.get("roomId")
    player_id = data.get("playerId")
    new_x = float(data.get("x", 50.0))
    new_x = max(10.0, min(90.0, new_x))

    with rooms_lock:
        if room_id not in rooms:
            return
        room = rooms[room_id]
        if room["currentTurnPlayerId"] != player_id:
            return
        if room["gameState"] != "playing":
            return
        room["claw"]["x"] = new_x

    emit("claw_moved", {"x": new_x, "by": player_id}, room=room_id, include_self=False)

@socketio.on("trigger_grab")
def on_trigger_grab(data):
    room_id = data.get("roomId")
    player_id = data.get("playerId")
    claw_x = float(data.get("x", 50.0))

    with rooms_lock:
        if room_id not in rooms:
            return
        room = rooms[room_id]
        if room["currentTurnPlayerId"] != player_id:
            return
        if room["gameState"] != "playing":
            return
        
        room["gameState"] = "grabbing"
        room["claw"]["state"] = "grabbing"
        room["claw"]["x"] = claw_x

    # Notify room that grab started
    socketio.emit("claw_grabbing", {"x": claw_x, "playerId": player_id}, room=room_id)

    # Determine caught plushie
    # Weighted random plushie
    roll = random.random()
    # Base catch rate is 70% if lined up
    catch_success = roll < 0.72

    caught_plushie = None
    is_legendary = False

    if catch_success:
        # Determine which plushie is caught (Legendary ~10%, Rare ~35%, Common ~55%)
        tier_roll = random.random()
        if tier_roll < 0.10:
            candidates = [p for p in PLUSHIES if p["rarity"] == "HUYỀN THOẠI"]
            is_legendary = True
        elif tier_roll < 0.45:
            candidates = [p for p in PLUSHIES if p["rarity"] == "HIẾM"]
        else:
            candidates = [p for p in PLUSHIES if p["rarity"] == "THƯỜNG"]
        
        caught_plushie = random.choice(candidates) if candidates else random.choice(PLUSHIES)
        if caught_plushie["rarity"] == "HUYỀN THOẠI":
            is_legendary = True

    def finish_grab_sequence():
        # Wait 3.5 seconds for grab animation to simulate dropping to chute
        time.sleep(3.5)
        with rooms_lock:
            if room_id in rooms:
                rooms[room_id]["gameState"] = "result"

        socketio.emit("grab_result", {
            "success": catch_success,
            "plushie": caught_plushie,
            "isLegendary": is_legendary,
            "playerId": player_id
        }, room=room_id)

        # After showing result for 4.5 seconds, switch to next turn
        time.sleep(4.5)
        advance_turn(room_id)

    threading.Thread(target=finish_grab_sequence, daemon=True).start()

@socketio.on("send_reaction")
def on_reaction(data):
    room_id = data.get("roomId")
    emoji = data.get("emoji", "💖")
    sender_name = data.get("senderName", "Bạn nhỏ")
    emit("reaction_received", {"emoji": emoji, "sender": sender_name}, room=room_id)

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    with rooms_lock:
        for room_id, room in rooms.items():
            player = next((p for p in room["players"] if p.get("socket_id") == sid), None)
            if player:
                player["connected"] = False
                player["disconnect_time"] = time.time()
                
                # If this player is currently taking turn, give them 12s to reconnect before auto-advance
                if room["currentTurnPlayerId"] == player["id"]:
                    room["disconnectionTurnExpire"] = time.time() + DISCONNECTED_TURN_TIME_LIMIT
                
                socketio.emit("player_connection_changed", {
                    "playerId": player["id"],
                    "name": player["name"],
                    "connected": False
                }, room=room_id)
                break

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print(">> CHIIKAWA CLAW MACHINE SERVER STARTED")
    print(f">> URL: http://0.0.0.0:{port}")
    print("=" * 60)
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
