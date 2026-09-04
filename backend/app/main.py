from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Quotation
from app.pdf import render_quotation_html
from app.routers import auth_router, customers, events, products, quotations
from app.routers.quotations import _with_relations
from app.schemas.schemas import QuotationOut

app = FastAPI(title="Viziwall Quotes API")

# Frontend and API are served from the same FastAPI process under the same origin
# (admin.viziwall.com), so there's no cross-origin request in production and no CORS
# middleware is needed. The Vite dev server (localhost:5173) talks to a separately
# running backend during local dev, but that's a same-machine convenience, not a
# real cross-origin production case.

app.include_router(auth_router.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(quotations.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}


# Short, stable, shareable URL for a quotation's printable view — e.g.
# /quote/vzw-2026-9017 — instead of the app's blob: preview tabs (which
# get a random, single-use URL from the browser, not the server). Must be
# registered before the SPA catch-all below, which would otherwise claim it.
# No app-level auth check here: this route is only reachable at all once
# Cloudflare Access has already required Google SSO login for the whole
# admin.viziwall.com domain, so the URL can stay clean with no token param.
@app.get("/quote/{quote_number}")
def view_quotation_by_number(quote_number: str, db: Session = Depends(get_db)):
    quotation = _with_relations(db.query(Quotation)).filter(Quotation.quote_number == quote_number.upper()).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    quotation_out = QuotationOut.model_validate(quotation)
    html_content = render_quotation_html(quotation_out)
    return Response(content=html_content, media_type="text/html")


# Serve the built frontend (frontend/dist, copied into the image at build time — see
# Dockerfile). Mounted last so it never shadows the /api/* or /health routes above.
frontend_dist = Path(__file__).resolve().parent.parent / "static"

if frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        # react-router (BrowserRouter) handles routing client-side, so every non-API,
        # non-asset path must still return index.html rather than a 404.
        requested = frontend_dist / full_path
        if full_path and requested.is_file():
            return FileResponse(requested)
        return FileResponse(frontend_dist / "index.html")
