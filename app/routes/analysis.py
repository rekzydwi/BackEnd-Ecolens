from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
import numpy as np
import tensorflow as tf
import io

router = APIRouter(prefix="/static-analysis", tags=["Analisis CO2"])

DATA_CO2 = {
    "Apple":                0.44,
    "Ayam Goreng":          5.70,
    "Bakso":                3.20,
    "Banana":               0.38,
    "Burger":               4.50,
    "Capcay":               0.60,
    "Chocolate Chip Cookie": 3.50,
    "Donat":                1.20,
    "Ikan Goreng":          3.29,
    "Kentang Goreng":       0.25,
    "Kiwi":                 0.50,
    "Mie Goreng":           1.50,
    "Nasi Goreng":          1.20,
    "Nasi Putih":           0.70,
    "Nugget":               2.40,
    "Pempek":               1.80,
    "Pineapples":           0.31,
    "Pizza":                2.80,
    "Rendang Sapi":         9.50,
    "Sate":                 5.00,
    "Spaghetti":            1.60,
    "Steak":               14.00,
    "Strawberry":           0.49,
    "Tahu Goreng":          0.66,
    "Telur Goreng":         1.60,
    "Telur Rebus":          1.60,
    "Tempe Goreng":         0.80,
    "Terong Balado":        0.46,
    "Tumis Kangkung":       0.40,
}

def kategori_dampak(co2: float) -> str:
    if co2 < 1.0:
        return "Rendah 🟢"
    elif co2 < 4.0:
        return "Sedang 🟡"
    else:
        return "Tinggi 🔴"

print("⏳ Memuat model AI...")
try:
    model = tf.keras.models.load_model("model/final_mobilenetv3_food_emission.keras")
    with open("model/class_names.txt", "r") as f:
        class_names = [line.strip() for line in f.readlines()]
    print(f"✅ Model berhasil dimuat! ({len(class_names)} kelas)")
except Exception as e:
    model = None
    class_names = []
    print(f"❌ Gagal memuat model: {e}")


@router.post("")
async def static_analysis(gambar: UploadFile = File(...)):
    """
    Analisis CO2 dari gambar makanan.
    Upload gambar makanan, dapatkan hasil klasifikasi dan emisi CO2-nya.
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model AI belum siap. Hubungi administrator."
        )

    if not gambar.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File harus berupa gambar (jpg, png, dll)"
        )

    isi_gambar = await gambar.read()
    img = Image.open(io.BytesIO(isi_gambar)).convert("RGB")
    img = img.resize((224, 224))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    prediksi = model.predict(img_array, verbose=0)
    indeks_terbaik = int(np.argmax(prediksi[0]))
    nama_makanan = class_names[indeks_terbaik]
    confidence = float(np.max(prediksi[0])) * 100

    # BATAS_CONFIDENCE = 60.0
    # if confidence < BATAS_CONFIDENCE:
    #     return {
    #         "makanan": None,
    #         "confidence": f"{confidence:.1f}%",
    #         "emisi_co2_kg": None,
    #         "kategori_dampak": None,
    #         "pesan": "Makanan tidak dapat dikenali dengan jelas. Coba foto dari sudut yang lebih jelas."
    #     }

    co2 = DATA_CO2.get(nama_makanan, 0.0)
    dampak = kategori_dampak(co2)

    return {
        "makanan": nama_makanan,
        "confidence": f"{confidence:.1f}%",
        "emisi_co2_kg": co2,
        "kategori_dampak": dampak,
        "pesan": f"Makanan ini menghasilkan {co2} kg CO2 per porsi"
    }