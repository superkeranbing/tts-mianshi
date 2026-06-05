from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json, asyncio, io, os, uuid, tempfile, random, logging

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)

# Buffer for audio chunks per connection
_buffers: dict[str, bytearray] = {}

@router.websocket("/asr/stream")
async def websocket_asr_stream(ws: WebSocket):
    await ws.accept()
    conn_id = str(uuid.uuid4())
    _buffers[conn_id] = bytearray()
    logger.info(f"WebSocket connected: {conn_id}")

    try:
        chunk_count = 0
        while True:
            data = await ws.receive()

            # Handle text messages (control)
            if data["type"] == "websocket.receive":
                text = data.get("text")
                if text:
                    try:
                        msg = json.loads(text)
                        if msg.get("type") == "ping":
                            await ws.send_text(json.dumps({"type": "pong"}))
                            continue
                        if msg.get("type") == "stop":
                            break
                    except json.JSONDecodeError:
                        pass
                    continue

                # Handle binary (audio data)
                bytes_data = data.get("bytes")
                if bytes_data:
                    _buffers[conn_id].extend(bytes_data)
                    chunk_count += 1

                    # Process every 10 chunks (roughly 2.5s of audio)
                    if chunk_count % 10 == 0:
                        partial = await _simulate_partial(_buffers[conn_id], chunk_count)
                        await ws.send_text(json.dumps(partial, ensure_ascii=False))

        # Final processing
        if len(_buffers[conn_id]) > 0:
            result = await _simulate_final(_buffers[conn_id])
            await ws.send_text(json.dumps(result, ensure_ascii=False))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conn_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
        except:
            pass
    finally:
        _buffers.pop(conn_id, None)


MOCK_PARTIALS = [
   "请简单介绍",
   "请简单介绍一下你自己",
   "能谈谈Rea",
   "能谈谈React的虚拟DOM原理吗",
   "你在项目中遇到的最大技术挑战",
   "你如何保证前端代码质量",
   "你对未来的职业规划",
   "你对未来的职业规划",
]

MOCK_SPEAKERS = ["面试官", "候选人", "面试官", "候选人", "面试官", "候选人", "面试官"]


async def _simulate_partial(buffer: bytearray, count: int) -> dict:
    """Simulate partial ASR result based on audio buffer"""
    idx = min(count // 10, len(MOCK_PARTIALS) - 1)
    dur_sec = len(buffer) / 16000 / 2  # rough wav duration
    return {
        "type": "partial_result",
        "text": MOCK_PARTIALS[idx] if idx < len(MOCK_PARTIALS) else "...",
        "is_final": False,
        "timestamp": round(dur_sec, 1),
    }


async def _simulate_final(buffer: bytearray) -> dict:
    """Simulate final ASR result"""
    dur_sec = len(buffer) / 16000 / 2  # rough wav duration
    return {
        "type": "final_result",
        "text": "你如何保证前端代码质量",
        "speaker": random.choice(MOCK_SPEAKERS),
        "is_final": True,
        "start_time": 0.0,
        "end_time": round(dur_sec, 1),
    }


