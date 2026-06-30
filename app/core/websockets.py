from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[str, list[WebSocket]]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        if user_id not in self.active_connections[room_id]:
            self.active_connections[room_id][user_id] = []
        self.active_connections[room_id][user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str, user_id: str):
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            if websocket in self.active_connections[room_id][user_id]:
                self.active_connections[room_id][user_id].remove(websocket)
            if not self.active_connections[room_id][user_id]:
                del self.active_connections[room_id][user_id]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for user_id, connections in list(self.active_connections[room_id].items()):
                for connection in list(connections):
                    try:
                        await connection.send_json(message)
                    except Exception:
                        self.disconnect(connection, room_id, user_id)


websocket_manager = ConnectionManager()
