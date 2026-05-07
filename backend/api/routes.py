from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from backend.config.config import get_settings
from backend.schemas import ChatRequest, ChatResponse, HealthResponse, StockSnapshot
from backend.services.functions.stock_data import get_stock_data
from backend.services.query_service import advisor


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", app=settings.app_name, ai_enabled=bool(settings.openai_api_key))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await advisor.ask(request.message, request.session_id)


@router.get("/stock/{symbol}", response_model=StockSnapshot)
async def stock_snapshot(symbol: str) -> StockSnapshot:
    try:
        return StockSnapshot(**get_stock_data(symbol))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch stock data for {symbol.upper()}") from exc


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "session", "session_id": None})

    try:
        while True:
            payload = await websocket.receive_json()
            message = str(payload.get("message", "")).strip()
            if not message:
                await websocket.send_json({"type": "error", "message": "Message is required"})
                continue

            async for token in advisor.stream(message):
                await websocket.send_json({"type": "token", "data": token})
            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        return
