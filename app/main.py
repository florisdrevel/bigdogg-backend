from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, products, overview, reports

app = FastAPI(
    title="Bigdogg API",
    description="Backend API for Bigdogg - Smart invoicing for Dutch freelancers",
    version="1.0.0",
    redirect_slashes=False
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(overview.router, prefix="/api/v1/overview", tags=["overview"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])

@app.get("/")
async def root():
    return {"message": "Bigdogg API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/debug-headers")
async def debug_headers(request: Request):
    return {"headers": dict(request.headers)}
