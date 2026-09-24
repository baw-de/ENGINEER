import os
from pathlib import Path

# Set server mode before importing engineer to disable GUI backend and CSV exports
os.environ["SERVER_MODE"] = "1"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse

from server.app.routes.flap_gate import router as flap_gate_router
from server.app.routes.labyrinth import router as labyrinth_router
from server.app.routes.operational import router as operational_router
from server.app.routes.plots import router as plots_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(
        title="ENGINEER Labyrinth API",
        description="REST API exposing hydraulic calculations from the ENGINEER package.",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        root_path=os.getenv("API_PREFIX", ""),
    )

    # CORS configuration from environment variable
    # In production/staging, set CORS_ORIGINS to specific domains
    # Example: CORS_ORIGINS=https://engineer-frontend.dokku.example.com,https://example.com
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    origins_list = [origin.strip() for origin in cors_origins.split(",")] if cors_origins != "*" else ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(labyrinth_router, prefix="/labyrinth", tags=["labyrinth"])
    app.include_router(flap_gate_router, prefix="/flap", tags=["flap"])
    app.include_router(operational_router, prefix="/operational", tags=["operational"])
    app.include_router(plots_router, tags=["plots"])

    # Serve Swagger UI assets as explicit endpoints (avoids StaticFiles + reverse proxy issues)
    @app.get("/static/swagger-ui-bundle.js", include_in_schema=False)
    async def swagger_ui_js():
        return FileResponse(STATIC_DIR / "swagger-ui-bundle.js", media_type="application/javascript")

    @app.get("/static/swagger-ui.css", include_in_schema=False)
    async def swagger_ui_css():
        return FileResponse(STATIC_DIR / "swagger-ui.css", media_type="text/css")

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="openapi.json",
            title=app.title + " - Swagger UI",
            swagger_js_url="static/swagger-ui-bundle.js",
            swagger_css_url="static/swagger-ui.css",
            swagger_favicon_url="data:,",
        )

    @app.get("/health", tags=["system"])
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
