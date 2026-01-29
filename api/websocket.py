"""WebSocket endpoints for real-time updates."""
import json
import asyncio
from typing import Set, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Store connected clients
connected_clients: Set[WebSocket] = set()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Send message to all connected clients."""
        if not self.active_connections:
            return

        message_json = json.dumps(message, default=str)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        self.active_connections -= disconnected

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception:
            self.disconnect(websocket)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)

    # Send welcome message
    await manager.send_personal(websocket, {
        "type": "connected",
        "payload": {"message": "Connected to Sportsbeams Pipeline"},
    })

    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()

            # Parse and handle client messages
            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "ping":
                    await manager.send_personal(websocket, {
                        "type": "pong",
                        "payload": {},
                    })
                elif message_type == "subscribe":
                    # Handle subscription requests (for future use)
                    await manager.send_personal(websocket, {
                        "type": "subscribed",
                        "payload": message.get("payload", {}),
                    })
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Helper functions for broadcasting events from other parts of the app
async def broadcast_prospect_created(prospect_id: str, name: str):
    """Broadcast when a new prospect is created."""
    await manager.broadcast({
        "type": "prospect_created",
        "payload": {"id": prospect_id, "name": name},
    })


async def broadcast_prospect_scored(prospect_id: str, score: int, tier: str):
    """Broadcast when a prospect is scored."""
    await manager.broadcast({
        "type": "prospect_scored",
        "payload": {"id": prospect_id, "score": score, "tier": tier},
    })


async def broadcast_research_completed(prospect_id: str, constraint: str):
    """Broadcast when research is completed."""
    await manager.broadcast({
        "type": "research_completed",
        "payload": {"id": prospect_id, "constraint": constraint},
    })


async def broadcast_email_sent(prospect_id: str, step: int):
    """Broadcast when an email is sent."""
    await manager.broadcast({
        "type": "email_sent",
        "payload": {"prospect_id": prospect_id, "step": step},
    })


async def broadcast_approval_needed(sequence_id: str, prospect_id: str):
    """Broadcast when approval is needed."""
    await manager.broadcast({
        "type": "approval_needed",
        "payload": {"sequence_id": sequence_id, "prospect_id": prospect_id},
    })


async def broadcast_agent_health(agent: str, status: str):
    """Broadcast agent health update."""
    await manager.broadcast({
        "type": "agent_health",
        "payload": {"agent": agent, "status": status},
    })
