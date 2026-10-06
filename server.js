const express = require('express');
const http = require('http');
const path = require('path');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: { origin: '*' }
});

const PORT = process.env.PORT || 5000;

// Serve static frontend assets
app.use(express.static(path.join(__dirname, 'static')));

// 20 Chiikawa plushies database
const PLUSHIES = [
    { id: "chiikawa", name: "Chiikawa", rarity: "THƯỜNG", rate: 0.65, color: "#FFF2F5", badge: "🧸" },
    { id: "hachiware", name: "Hachiware", rarity: "THƯỜNG", rate: 0.65, color: "#E3F2FD", badge: "🐱" },
    { id: "usagi", name: "Usagi", rarity: "THƯỜNG", rate: 0.60, color: "#FFF9C4", badge: "🐰" },
    { id: "kurimanju", name: "Kurimanju", rarity: "THƯỜNG", rate: 0.60, color: "#EFEBE9", badge: "🌰" },
    { id: "shisa", name: "Shisa", rarity: "THƯỜNG", rate: 0.55, color: "#FFF3E0", badge: "🦁" },
    { id: "armor_worker", name: "Armor-san Lao Động", rarity: "THƯỜNG", rate: 0.55, color: "#ECEFF1", badge: "🛡️" },
    { id: "armor_ramen", name: "Armor-san Tiệm Mì", rarity: "THƯỜNG", rate: 0.55, color: "#FFF8E1", badge: "🍜" },
    { id: "goblin", name: "Goblin Xanh", rarity: "THƯỜNG", rate: 0.50, color: "#E8F5E9", badge: "👺" },
    
    { id: "momonga", name: "Momonga", rarity: "HIẾM", rate: 0.38, color: "#F3E5F5", badge: "🐿️" },
    { id: "rakko", name: "Rakko Thầy Kiếm Sĩ", rarity: "HIẾM", rate: 0.35, color: "#E0F7FA", badge: "🦦" },
    { id: "pajama_chiikawa", name: "Pajama Chiikawa", rarity: "HIẾM", rate: 0.35, color: "#FCE4EC", badge: "🎀" },
    { id: "pajama_hachiware", name: "Pajama Hachiware", rarity: "HIẾM", rate: 0.35, color: "#E1F5FE", badge: "💤" },
    { id: "pajama_usagi", name: "Pajama Usagi", rarity: "HIẾM", rate: 0.35, color: "#FFFDE7", badge: "⭐" },
    { id: "chii_kabuto", name: "Chii-Kabuto Bọ Nhỏ", rarity: "HIẾM", rate: 0.32, color: "#EDE7F6", badge: "🪲" },
    { id: "star_hoshi", name: "Hoshi Sao Băng", rarity: "HIẾM", rate: 0.30, color: "#FFF9C4", badge: "🌟" },
    { id: "chiikawa_mage", name: "Chiikawa Pháp Sư", rarity: "HIẾM", rate: 0.28, color: "#F8BBD0", badge: "🪄" },
    { id: "beetle_leaf", name: "Bọ Lá Xanh Bạn", rarity: "HIẾM", rate: 0.30, color: "#DCEDC8", badge: "🍃" },
    
    { id: "legend_usagi", name: "Usagi Chiến Thần Yahaha", rarity: "HUYỀN THOẠI", rate: 0.16, color: "#FFE082", badge: "⚡" },
    { id: "legend_momonga", name: "Momonga Nữ Hoàng Vương Miện", rarity: "HUYỀN THOẠI", rate: 0.14, color: "#E1BEE7", badge: "👑" },
    { id: "legend_golden_chiikawa", name: "Golden Chiikawa Thần Tài", rarity: "HUYỀN THOẠI", rate: 0.12, color: "#FFD54F", badge: "🏆" }
];

app.get('/api/plushies', (req, res) => {
    res.json(PLUSHIES);
});

// Rooms database
const rooms = {};
const DISCONNECT_GRACE_PERIOD = 50 * 1000; // 50 seconds (Section 23)
const TURN_TIME_LIMIT = 25 * 1000;         // 25 seconds
const DISCONNECTED_TURN_LIMIT = 8 * 1000;  // 8 seconds

function getRoomSummary(room) {
    const now = Date.now();
    return {
        id: room.id,
        name: room.name,
        gameState: room.gameState,
        currentTurnPlayerId: room.currentTurnPlayerId,
        turnTimer: room.turnEndTime ? Math.max(0, Math.round((room.turnEndTime - now) / 1000)) : 0,
        claw: room.claw,
        players: room.players.map(p => ({
            id: p.id,
            name: p.name,
            connected: p.connected,
            coins: p.coins,
            isTurn: p.id === room.currentTurnPlayerId
        }))
    };
}

function advanceTurn(roomId) {
    const room = rooms[roomId];
    if (!room) return;

    const connectedPlayers = room.players.filter(p => p.connected);
    if (connectedPlayers.length === 0) {
        room.currentTurnPlayerId = null;
        room.gameState = 'waiting';
        room.turnEndTime = 0;
        return;
    }

    const currentId = room.currentTurnPlayerId;
    let currentIdx = room.players.findIndex(p => p.id === currentId);

    let nextPlayer = null;
    for (let step = 1; step <= room.players.length; step++) {
        const targetIdx = (currentIdx + step) % room.players.length;
        const candidate = room.players[targetIdx];
        if (candidate.connected) {
            nextPlayer = candidate;
            break;
        }
    }

    if (nextPlayer) {
        room.currentTurnPlayerId = nextPlayer.id;
        room.gameState = 'playing';
        room.turnEndTime = Date.now() + TURN_TIME_LIMIT;
        room.claw = { x: 50.0, state: 'idle', open: true };
    } else {
        room.currentTurnPlayerId = null;
        room.gameState = 'waiting';
        room.turnEndTime = 0;
    }

    io.to(roomId).emit('room_state_update', getRoomSummary(room));
}

// Background monitor for turns and Section 23 disconnect timeout
setInterval(() => {
    const now = Date.now();
    for (const roomId in rooms) {
        const room = rooms[roomId];
        
        // 1. Remove players disconnected longer than grace period
        const playersToRemove = [];
        room.players.forEach(p => {
            if (!p.connected && p.disconnectTime && (now - p.disconnectTime > DISCONNECT_GRACE_PERIOD)) {
                playersToRemove.push(p);
            }
        });

        playersToRemove.forEach(p => {
            const idx = room.players.indexOf(p);
            if (idx !== -1) room.players.splice(idx, 1);
            io.to(roomId).emit('player_left_permanently', { playerId: p.id, name: p.name });
            if (room.currentTurnPlayerId === p.id) {
                advanceTurn(roomId);
            }
        });

        if (room.players.length === 0) {
            delete rooms[roomId];
            continue;
        }

        // 2. Turn expiry
        if (room.gameState === 'playing' && room.turnEndTime) {
            const currentP = room.players.find(p => p.id === room.currentTurnPlayerId);
            if (!currentP || !currentP.connected) {
                if (room.disconnectionTurnExpire && now > room.disconnectionTurnExpire) {
                    room.disconnectionTurnExpire = null;
                    advanceTurn(roomId);
                }
            } else if (now >= room.turnEndTime) {
                advanceTurn(roomId);
            }
        }
    }
}, 1000);

io.on('connection', (socket) => {
    
    // Create Room
    socket.on('create_room', (data) => {
        const playerId = data.playerId;
        const playerName = data.playerName || 'Người chơi Chiikawa';
        const roomName = data.roomName || `Tiệm Gắp ${Math.floor(100 + Math.random() * 900)}`;
        const roomId = `CHII-${Math.floor(1000 + Math.random() * 9000)}`;

        const room = {
            id: roomId,
            name: roomName,
            gameState: 'playing',
            currentTurnPlayerId: playerId,
            turnEndTime: Date.now() + TURN_TIME_LIMIT,
            claw: { x: 50.0, state: 'idle', open: true },
            players: [
                {
                    id: playerId,
                    name: playerName,
                    socketId: socket.id,
                    connected: true,
                    coins: data.coins || 10,
                    disconnectTime: null
                }
            ]
        };

        rooms[roomId] = room;
        socket.join(roomId);
        socket.emit('room_created', { roomId, room: getRoomSummary(room) });
    });

    // Join Room
    socket.on('join_room', (data) => {
        const roomId = (data.roomId || '').trim().toUpperCase();
        const playerId = data.playerId;
        const playerName = data.playerName || 'Khách gắp thú';

        if (!rooms[roomId]) {
            socket.emit('error_message', { message: `Không tìm thấy phòng ${roomId}! Hãy kiểm tra lại mã phòng.` });
            return;
        }

        const room = rooms[roomId];
        const existing = room.players.find(p => p.id === playerId);
        if (existing) {
            existing.socketId = socket.id;
            existing.connected = true;
            existing.disconnectTime = null;
        } else {
            room.players.push({
                id: playerId,
                name: playerName,
                socketId: socket.id,
                connected: true,
                coins: data.coins || 10,
                disconnectTime: null
            });
            if (!room.currentTurnPlayerId) {
                room.currentTurnPlayerId = playerId;
                room.gameState = 'playing';
                room.turnEndTime = Date.now() + TURN_TIME_LIMIT;
            }
        }

        socket.join(roomId);
        socket.emit('joined_room_success', { roomId, room: getRoomSummary(room) });
        io.to(roomId).emit('room_state_update', getRoomSummary(room));
    });

    // Section 23: Reconnect Player
    socket.on('reconnect_player', (data) => {
        const { roomId, playerId, playerName } = data;
        const room = rooms[roomId];

        if (!room) {
            socket.emit('reconnect_failed', { message: 'Phòng không tồn tại hoặc đã hết hạn.' });
            return;
        }

        const player = room.players.find(p => p.id === playerId);
        if (!player) {
            socket.emit('reconnect_failed', { message: 'Người chơi không còn trong phòng này.' });
            return;
        }

        player.socketId = socket.id;
        player.connected = true;
        player.disconnectTime = null;
        if (room.disconnectionTurnExpire) room.disconnectionTurnExpire = null;

        socket.join(roomId);
        const summary = getRoomSummary(room);
        socket.emit('reconnected_success', {
            room: summary,
            player: player,
            gameState: room.gameState,
            currentTurn: room.currentTurnPlayerId,
            claw: room.claw,
            players: summary.players
        });
        io.to(roomId).emit('room_state_update', summary);
    });

    // Claw movement
    socket.on('move_claw', (data) => {
        const { roomId, playerId, x } = data;
        const room = rooms[roomId];
        if (!room || room.currentTurnPlayerId !== playerId || room.gameState !== 'playing') return;

        const newX = Math.max(10, Math.min(90, parseFloat(x)));
        room.claw.x = newX;
        socket.to(roomId).emit('claw_moved', { x: newX, by: playerId });
    });

    // Trigger grab
    socket.on('trigger_grab', (data) => {
        const { roomId, playerId, x } = data;
        const room = rooms[roomId];
        if (!room || room.currentTurnPlayerId !== playerId || room.gameState !== 'playing') return;

        const clawX = parseFloat(x);
        room.gameState = 'grabbing';
        room.claw.state = 'grabbing';
        room.claw.x = clawX;

        io.to(roomId).emit('claw_grabbing', { x: clawX, playerId });

        const catchSuccess = Math.random() < 0.72;
        let caughtPlushie = null;
        let isLegendary = false;

        if (catchSuccess) {
            const tierRoll = Math.random();
            let candidates;
            if (tierRoll < 0.10) {
                candidates = PLUSHIES.filter(p => p.rarity === 'HUYỀN THOẠI');
                isLegendary = true;
            } else if (tierRoll < 0.45) {
                candidates = PLUSHIES.filter(p => p.rarity === 'HIẾM');
            } else {
                candidates = PLUSHIES.filter(p => p.rarity === 'THƯỜNG');
            }
            caughtPlushie = candidates[Math.floor(Math.random() * candidates.length)] || PLUSHIES[0];
            if (caughtPlushie.rarity === 'HUYỀN THOẠI') isLegendary = true;
        }

        setTimeout(() => {
            if (rooms[roomId]) rooms[roomId].gameState = 'result';
            io.to(roomId).emit('grab_result', {
                success: catchSuccess,
                plushie: caughtPlushie,
                isLegendary,
                playerId
            });

            setTimeout(() => {
                advanceTurn(roomId);
            }, 4500);
        }, 3500);
    });

    // Reactions
    socket.on('send_reaction', (data) => {
        const { roomId, emoji, senderName } = data;
        io.to(roomId).emit('reaction_received', { emoji: emoji || '💖', sender: senderName || 'Bạn nhỏ' });
    });

    // Disconnect
    socket.on('disconnect', () => {
        for (const roomId in rooms) {
            const room = rooms[roomId];
            const player = room.players.find(p => p.socketId === socket.id);
            if (player) {
                player.connected = false;
                player.disconnectTime = Date.now();

                if (room.currentTurnPlayerId === player.id) {
                    room.disconnectionTurnExpire = Date.now() + DISCONNECTED_TURN_LIMIT;
                }

                io.to(roomId).emit('player_connection_changed', {
                    playerId: player.id,
                    name: player.name,
                    connected: false
                });
                break;
            }
        }
    });
});

server.listen(PORT, () => {
    console.log('============================================================');
    console.log(`>> Node.js + Express + Socket.IO Server running on port ${PORT}`);
    console.log(`>> URL: http://127.0.0.1:${PORT}`);
    console.log('============================================================');
});
