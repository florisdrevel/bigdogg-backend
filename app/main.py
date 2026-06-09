from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import auth, products, clients, invoices, ai, expenses, overview, profile, subscription, pdf, email, reports, annual_report
from app.routers import import_invoices
from app.routers import payments
from app.routers import hours, investments, projects
from app.routers import support
from app.routers import reminders
from app.routers import referrals
from app.routers import quotes
from app.routers import banking
from app.routers import notifications
from app.routers import devices
from app.routers import share
from app.routers import accountants
from app.routers import bank
from app.routers import downloads
import os


app = FastAPI(
    title="Bigdogg. API",
    description="Backend API for Bigdogg - Smart invoicing for Dutch freelancers",
    version="1.0.0",
    redirect_slashes=False
)

# CORS — only the production web origins + localhost for dev. Native
# (Android / iOS) apps and Stripe webhooks don't send an Origin header
# so CORS rules never apply to them. Bearer tokens travel in
# Authorization headers, not cookies, so allow_credentials is left off.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bigdogg.nl",
        "https://www.bigdogg.nl",
        "https://bigdogg-production.up.railway.app",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(annual_report.router, prefix="/api/v1/reports", tags=["annual_report"])
# Invoice import routes (import-invoices, imported, delete imported)
app.include_router(import_invoices.router, prefix="/api/v1/invoices", tags=["import"])
# Expense import route
app.include_router(import_invoices.router, prefix="/api/v1/expenses", tags=["import-expenses"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(hours.router, prefix="/api/v1/hours", tags=["hours"])
app.include_router(investments.router, prefix="/api/v1/investments", tags=["investments"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(support.router, prefix="/api/v1/support", tags=["support"])
app.include_router(reminders.router, prefix="/api/v1/reminders", tags=["reminders"])
app.include_router(referrals.router, prefix="/api/v1/referrals", tags=["referrals"])
app.include_router(quotes.router, prefix="/api/v1/quotes", tags=["quotes"])
app.include_router(banking.router, prefix="/api/v1/banking", tags=["banking"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
# Public share-link landing pages (rendered HTML for OG previews,
# redirect into the SPA for humans). Mounted at root, NO /api prefix.
app.include_router(share.router, tags=["share"])
app.include_router(accountants.router, prefix="/api/v1/accountants", tags=["accountants"])
app.include_router(bank.router, prefix="/api/v1/bank", tags=["bank"])
app.include_router(downloads.router, prefix="/api/v1/downloads", tags=["downloads"])


@app.get("/health")
async def health():
    # Expose the deployed commit + a build marker so a deploy can be
    # verified from outside (Railway injects RAILWAY_GIT_COMMIT_SHA). The
    # marker string bumps with each deploy-debug build so we can tell which
    # code is actually running without an authenticated call.
    return {
        "status": "healthy",
        "commit": (os.getenv("RAILWAY_GIT_COMMIT_SHA") or "unknown")[:8],
        "build_marker": "bank-default-open-v1",
    }

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
