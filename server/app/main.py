import os

# Set server mode before importing engineer to disable GUI backend and CSV exports
os.environ["SERVER_MODE"] = "1"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.app.routes.flap_gate import router as flap_gate_router
from server.app.routes.labyrinth import router as labyrinth_router
from server.app.routes.operational import router as operational_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="ENGINEER Labyrinth API",
        description="REST API exposing hydraulic calculations from the ENGINEER package.",
        version="0.1.0",
    )

    # In production, restrict allow_origins to specific domains
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(labyrinth_router, prefix="/labyrinth", tags=["labyrinth"])
    app.include_router(flap_gate_router, prefix="/flap", tags=["flap"])
    app.include_router(operational_router, prefix="/operational", tags=["operational"])
    return app


app = create_app()
