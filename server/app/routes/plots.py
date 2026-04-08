from typing import Annotated

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import Response

try:
    # Works when imported as server.app.routes.*
    from server.app.routes.utils.plot_helpers import generate_geometry_plot_svg
except ModuleNotFoundError:
    # Fallback for flatter package layouts.
    from .utils.plot_helpers import generate_geometry_plot_svg

router = APIRouter(prefix="/plots")


@router.get(
    "/{plot_id}",
    response_class=Response,
    summary="Get geometry plot as SVG",
    description="Returns the labyrinth geometry plot as SVG with strong caching headers.",
    responses={
        200: {"description": "SVG plot image", "content": {"image/svg+xml": {}}},
        404: {"description": "Plot could not be generated"},
        500: {"description": "Internal server error during plot generation"},
    },
)
def get_plot(
    plot_id: Annotated[str, Path(description="Plot identifier (e.g. 'labyrinth' or 'optimize-abc123')")],
) -> Response:
    # endpoint for getting the geometry plot as SVG
    try:
        svg_bytes = generate_geometry_plot_svg(plot_id)
        if not svg_bytes:
            raise HTTPException(
                status_code=404,
                detail="Plot could not be generated. Check server logs.",
            )

        return Response(
            content=svg_bytes,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "public, max-age=3600, immutable",
                "Content-Disposition": f'inline; filename="labyrinth-geometry-{plot_id}.svg"',
                "X-Content-Type-Options": "nosniff",
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate plot: {str(exc)}",
        ) from exc
