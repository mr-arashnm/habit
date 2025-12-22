from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from ..dependencies import get_current_user_from_token
from app.managers.notifications_manager import manager

router = APIRouter()


@router.websocket("/notifications/{token}")
async def notification_websocket(websocket: WebSocket, token: str):
    # تایید هویت کاربر
    user = await get_current_user_from_token(token)

    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # اتصال به مدیر نوتیفیکیشن
    await manager.connect(user.id, websocket)

    try:
        # حلقه باز نگه داشتن اتصال
        while True:
            # منتظر پیام (اختیاری) - مثلا برای Heartbeat
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)