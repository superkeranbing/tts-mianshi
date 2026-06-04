from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json, asyncio, random

router = APIRouter(prefix="/ws", tags=["WebSocket"])

MOCK_STREAM = [
    "请简单介",
    "请简单介绍一下",
    "请简单介绍一下你自己。",
]

@router.websocket("/asr/stream")
async def websocket_asr_stream(ws: WebSocket):
    await ws.accept()
    try:
        full_text = ""
        while True:
            data = await ws.receive()
            if data["type"] == "websocket.receive":
                chunk_type = data.get("text")
                if chunk_type == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
                    continue

            # Simulate streaming ASR
            for partial in MOCK_STREAM:
                await asyncio.sleep(0.8)
                await ws.send_text(json.dumps({
                    "type": "partial_result",
                    "text": partial,
                    "is_final": partial == MOCK_STREAM[-1],
                    "timestamp": random.uniform(0, 30)
                }, ensure_ascii=False))

            # Send final result with speaker info
            await asyncio.sleep(0.5)
            full_text = MOCK_STREAM[-1]
            await ws.send_text(json.dumps({
                "type": "final_result",
                "text": full_text,
                "speaker": "面试官",
                "is_final": True,
                "start_time": 0.0,
                "end_time": 3.5
            }, ensure_ascii=False))

            break
    except WebSocketDisconnect:
        pass
