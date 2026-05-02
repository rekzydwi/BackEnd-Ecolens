from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter(tags=["Realtime"])


@router.websocket("/realtime-cam")
async def realtime_cam(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Client terhubung")

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "error": "Format salah. Kirim JSON dengan field 'image'"
                }))
                continue

            if not payload.get("image"):
                await websocket.send_text(json.dumps({
                    "error": "Field 'image' tidak boleh kosong"
                }))
                continue

            # TODO: Hasil model ai nanti disini.
            response = {
                "object": "unknown",
                "co2_kg": 0.0,
                "label": "Belum terklasifikasi",
                "note": "Model AI belum diintegrasikan"
            }
            await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        print("[WS] Client disconnect")