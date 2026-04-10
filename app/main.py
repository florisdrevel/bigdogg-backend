from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import auth, products, clients, invoices, ai, expenses, overview, profile, subscription, pdf, email
import os

app = FastAPI(
    title="Bigdogg. API",
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
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["invoices"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["expenses"])
app.include_router(overview.router, prefix="/api/v1/overview", tags=["overview"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["profile"])
app.include_router(subscription.router, prefix="/api/v1/subscription", tags=["subscription"])
app.include_router(pdf.router, prefix="/api/v1/pdf", tags=["pdf"])
app.include_router(email.router, prefix="/api/v1/email", tags=["email"])

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/debug-headers")
async def debug_headers(request: Request):
    return {"headers": dict(request.headers)}

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    async def root():
        return {"message": "Bigdogg API is running", "version": "1.0.0"}