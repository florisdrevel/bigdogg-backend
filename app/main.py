from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth

app = FastAPI(
    title="Bigdogg API",
    description="Backend API for Bigdogg - Smart invoicing for Dutch freelancers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Bigdogg API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}