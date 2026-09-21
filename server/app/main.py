import os
from pathlib import Path

# Set server mode before importing engineer to disable GUI backend and CSV exports
os.environ["SERVER_MODE"] = "1"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

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

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )

    @app.get("/health", tags=["system"])
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
