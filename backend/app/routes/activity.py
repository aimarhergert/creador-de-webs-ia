import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.dependencies import get_current_user
from app.models.activity import ActivityEvent, EventType
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = {}  # user_id -> [ws]
        self._global: list[WebSocket] = []  # unauthenticated / admin feeds

    async def connect(self, ws: WebSocket, user_id: Optional[int] = None):
        await ws.accept()
        if user_id:
            self._connections.setdefault(user_id, []).append(ws)
        else:
            self._global.append(ws)

    def disconnect(self, ws: WebSocket, user_id: Optional[int] = None):
        if user_id and user_id in self._connections:
            self._connections[user_id] = [c for c in self._connections[user_id] if c != ws]
        else:
            self._global = [c for c in self._global if c != ws]

    async def broadcast_to_user(self, user_id: int, data: dict):
        dead = []
        for ws in self._connections.get(user_id, []):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, user_id)

    async def broadcast_global(self, data: dict):
        dead = []
        for ws in self._global:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast_all(self, data: dict):
        await self.broadcast_global(data)
        for uid in list(self._connections.keys()):
            await self.broadcast_to_user(uid, data)


manager = ConnectionManager()


class EventOut(BaseModel):
    id: int
    user_id: int | None
    asset_id: int | None
    event_type: str
    title: str
    description: str | None
    data: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[EventOut])
async def get_activity(
    limit: int = Query(50, le=200),
    event_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(ActivityEvent).order_by(desc(ActivityEvent.created_at)).limit(limit)
    if event_type:
        q = q.where(ActivityEvent.event_type == event_type)
    result = await db.execute(q)
    events = result.scalars().all()
    return [
        EventOut(
            id=e.id, user_id=e.user_id, asset_id=e.asset_id,
            event_type=e.event_type.value, title=e.title,
            description=e.description, data=e.data, created_at=e.created_at,
        )
        for e in events
    ]


@router.websocket("/ws")
async def websocket_feed(
    ws: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket activity feed.
    Connect with: ws://localhost:8000/api/activity/ws?token=<jwt>
    Emits JSON events in real-time as they are created.
    """
    user_id: Optional[int] = None

    if token:
        try:
            from app.services.auth_service import decode_token
            payload = decode_token(token)
            if payload.get("type") == "access":
                user_id = int(payload.get("sub", 0)) or None
        except Exception:
            pass

    await manager.connect(ws, user_id)
    try:
        # Send last 10 events as initial state
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ActivityEvent).order_by(desc(ActivityEvent.created_at)).limit(10)
            )
            events = result.scalars().all()
            for e in reversed(events):
                await ws.send_json({
                    "id": e.id,
                    "event_type": e.event_type.value,
                    "title": e.title,
                    "description": e.description,
                    "data": e.data,
                    "created_at": e.created_at.isoformat(),
                    "backfill": True,
                })

        while True:
            # Keep connection alive — client can send pings
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await ws.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(ws, user_id)
    except Exception as exc:
        logger.warning("WS disconnected: %s", exc)
        manager.disconnect(ws, user_id)


async def emit_event(
    event_type: EventType,
    title: str,
    description: Optional[str] = None,
    data: Optional[dict] = None,
    user_id: Optional[int] = None,
    asset_id: Optional[int] = None,
):
    """Save event to DB and push via WebSocket."""
    async with AsyncSessionLocal() as db:
        event = ActivityEvent(
            user_id=user_id,
            asset_id=asset_id,
            event_type=event_type,
            title=title,
            description=description,
            data=data,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

    payload = {
        "id": event.id,
        "event_type": event.event_type.value,
        "title": event.title,
        "description": event.description,
        "data": event.data,
        "created_at": event.created_at.isoformat(),
    }
    await manager.broadcast_all(payload)
    return event
