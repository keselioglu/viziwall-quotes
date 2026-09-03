from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth_router, customers, events, products, quotations

app = FastAPI(title="Viziwall Quotes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server; add prod frontend URL after deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(customers.router)
app.include_router(events.router)
app.include_router(products.router)
app.include_router(quotations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
