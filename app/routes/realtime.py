from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.routes.analysis import model, class_names, df_emisi, cari_emisi, kategori_dampak, normalize_text
import numpy as np
import tensorflow as tf
from PIL import Image
import base64
import json
import io

router = APIRouter(tags=["Realtime"])


@router.websocket("/realtime-cam")
async def realtime_cam(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Client terhubung")

    try:
        while True:
            data = await websocket.receive_text()

            if not data or len(data) < 100:
                await websocket.send_text(json.dumps({
                    "error": "Data gambar tidak valid"
                }))
                continue

            try:
                image_bytes = base64.b64decode(data)
                img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                img = img.resize((224, 224))
                img_array = np.array(img, dtype=np.float32)
                img_array = tf.keras.applications.mobilenet_v3.preprocess_input(img_array)
                img_array = np.expand_dims(img_array, axis=0)

                prediksi = model.predict(img_array, verbose=0)[0]
                indeks = int(np.argmax(prediksi))
                nama_makanan = class_names[indeks]
                confidence = float(prediksi[indeks]) * 100

                if confidence < 60.0:
                    await websocket.send_text(json.dumps({
                        "makanan": None,
                        "confidence": f"{confidence:.1f}%",
                        "emisi_co2_kg": None,
                        "kategori_dampak": None,
                        "pesan": "Makanan tidak dapat dikenali. Arahkan kamera lebih jelas."
                    }))
                    continue

                hasil_emisi = cari_emisi(nama_makanan, df_emisi)

                if hasil_emisi:
                    await websocket.send_text(json.dumps({
                        "makanan": nama_makanan,
                        "confidence": f"{confidence:.1f}%",
                        "emisi_co2_kg": hasil_emisi["emisi"],
                        "kategori": hasil_emisi["kategori"],
                        "kategori_dampak": kategori_dampak(hasil_emisi["emisi"]),
                        "pesan": f"Makanan ini menghasilkan {hasil_emisi['emisi']} kg CO2 per porsi"
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "makanan": nama_makanan,
                        "confidence": f"{confidence:.1f}%",
                        "emisi_co2_kg": None,
                        "kategori_dampak": None,
                        "pesan": "Makanan terdeteksi tapi data CO2 belum tersedia."
                    }))

            except Exception as e:
                await websocket.send_text(json.dumps({
                    "error": f"Gagal memproses gambar: {str(e)}"
                }))

    except WebSocketDisconnect:
        print("[WS] Client disconnect")