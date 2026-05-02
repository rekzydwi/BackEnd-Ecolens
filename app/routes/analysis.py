from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
import numpy as np
import tensorflow as tf
import pandas as pd
import difflib
import io

router = APIRouter(prefix="/static-analysis", tags=["Analisis CO2"])

def normalize_text(text):
    text = str(text).lower().strip()
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = " ".join(text.split())
    return text

def cari_emisi(nama_makanan: str, df: pd.DataFrame):
    nama_norm = normalize_text(nama_makanan)
    
    # Coba exact match
    exact = df[df["nama_norm"] == nama_norm]
    if len(exact) > 0:
        row = exact.iloc[0]
        return {"nama": row["nama"], "emisi": float(row["emisi"]), "kategori": row["kategori"], "tipe": "Exact Match"}
    
    # Kalau tidak ketemu, pakai fuzzy match
    available = df["nama_norm"].tolist()
    cocok = difflib.get_close_matches(nama_norm, available, n=1, cutoff=0.60)
    if cocok:
        row = df[df["nama_norm"] == cocok[0]].iloc[0]
        return {"nama": row["nama"], "emisi": float(row["emisi"]), "kategori": row["kategori"], "tipe": "Fuzzy Match"}
    
    return None

def kategori_dampak(co2: float) -> str:
    if co2 < 1.0:
        return "Rendah 🟢"
    elif co2 < 4.0:
        return "Sedang 🟡"
    else:
        return "Tinggi 🔴"
        
print("⏳ Memuat model AI dan data emisi...")
try:
    model = tf.keras.models.load_model("model/final_mobilenetv3_food_emission.keras")
    
    with open("model/class_names.txt", "r") as f:
        class_names = [line.strip() for line in f.readlines()]
    
    df_emisi = pd.read_csv("model/dataset_footprint_emission.csv")
    df_emisi["emisi"] = pd.to_numeric(df_emisi["emisi"], errors="coerce")
    df_emisi = df_emisi.dropna(subset=["emisi"])
    df_emisi["nama_norm"] = df_emisi["nama"].apply(normalize_text)
    
    print(f"✅ Model berhasil dimuat! ({len(class_names)} kelas)")
    print(f"✅ Data emisi berhasil dimuat! ({len(df_emisi)} baris)")
except Exception as e:
    model = None
    class_names = []
    df_emisi = None
    print(f"❌ Gagal memuat: {e}")


@router.post("")
async def static_analysis(gambar: UploadFile = File(...)):
    """
    Analisis CO2 dari gambar makanan.
    Upload gambar makanan, dapatkan hasil klasifikasi dan estimasi CO2.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model AI belum siap.")

    if not gambar.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar.")

    isi_gambar = await gambar.read()
    img = Image.open(io.BytesIO(isi_gambar)).convert("RGB")
    img = img.resize((224, 224))
    img_array = np.array(img, dtype=np.float32)
    img_array = tf.keras.applications.mobilenet_v3.preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)
    
    prediksi = model.predict(img_array, verbose=0)[0]
    indeks = int(np.argmax(prediksi))
    nama_makanan = class_names[indeks]
    confidence = float(prediksi[indeks]) * 100

    if confidence < 60.0:
        return {
            "makanan": None,
            "confidence": f"{confidence:.1f}%",
            "emisi_co2_kg": None,
            "kategori_dampak": None,
            "pesan": "Makanan tidak dapat dikenali. Coba foto dari sudut yang lebih jelas."
        }

    hasil_emisi = cari_emisi(nama_makanan, df_emisi)

    if hasil_emisi:
        return {
            "makanan": nama_makanan,
            "confidence": f"{confidence:.1f}%",
            "emisi_co2_kg": hasil_emisi["emisi"],
            "kategori": hasil_emisi["kategori"],
            "kategori_dampak": kategori_dampak(hasil_emisi["emisi"]),
            "tipe_pencocokan": hasil_emisi["tipe"],
            "pesan": f"Makanan ini menghasilkan {hasil_emisi['emisi']} kg CO2 per porsi"
        }
    else:
        return {
            "makanan": nama_makanan,
            "confidence": f"{confidence:.1f}%",
            "emisi_co2_kg": None,
            "kategori_dampak": None,
            "pesan": "Makanan terdeteksi tapi data CO2 belum tersedia."
        }
