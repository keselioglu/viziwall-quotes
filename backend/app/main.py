from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import auth_router, customers, events, products, quotations

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
