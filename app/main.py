from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, Base
from app.models import user          # noqa: F401
from app.models import scan_result   # noqa: F401
from app.routes.auth import router as auth_router
from app.routes.realtime import router as realtime_router
from app.routes.analysis import router as analysis_router
from app.routes.result import router as result_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EcoLens API",
    description="Backend API untuk EcoLens — AI-Powered CO2 Footprint Scanner",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(realtime_router)
app.include_router(analysis_router)
app.include_router(result_router)

@app.get("/", tags=["Health"])
def root():
    return {"message": "EcoLens Backend Running", "status": "ok"}