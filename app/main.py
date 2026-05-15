from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analysis import router as analysis_router
from app.routes.realtime import router as realtime_router

app = FastAPI(
    title="EcoLens AI Service",
    description="AI Service untuk EcoLens — Klasifikasi makanan dan estimasi CO2 menggunakan MobileNetV3",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)
app.include_router(realtime_router)

@app.get("/", tags=["Health"])
def root():
    return {"message": "EcoLens AI Service Running", "status": "ok"}