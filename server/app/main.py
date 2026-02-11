import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


def _parse_origins(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app() -> FastAPI:
    app = FastAPI(title="ai-ipvoyage API", version="0.1.0")

    # Initialize database connection pool
    from app.core.database import init_db_pool
    try:
        init_db_pool()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Make sure DATABASE_URL is set in your .env file")

    client_origins = _parse_origins(os.getenv("CLIENT_URL"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=client_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/")
    def root() -> dict:
        return {"message": "Welcome to ai-ipvoyage API"}

    from app.routes.auth import router as auth_router
    app.include_router(auth_router)

    @app.on_event("shutdown")
    def shutdown_event():
        """Close database connections on app shutdown."""
        from app.core.database import close_db_pool
        close_db_pool()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
