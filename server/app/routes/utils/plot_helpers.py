import contextlib
import io
from typing import Any

import matplotlib.pyplot as plt

_PLOT_OBJECTS: dict[str, Any] = {}


def store_plot_source(plot_id: str, obj: Any) -> None:
    # Stores the latest computed object for a plot ID.
    _PLOT_OBJECTS[plot_id] = obj


def generate_geometry_plot_svg(plot_id: str = "default") -> bytes | None:
    # Generates SVG bytes for the plot ID, or None if no source is available.
    try:
        # Prefer rendering from the latest cached backend object.
        cached_obj = _PLOT_OBJECTS.get(plot_id)
        if cached_obj is not None and hasattr(cached_obj, "plot_geometry"):
            with contextlib.redirect_stdout(io.StringIO()):
                cached_obj.plot_geometry()
            svg_bytes = getattr(cached_obj, "_last_geometry_svg_bytes", None)
            if svg_bytes:
                return svg_bytes

        return None
    except Exception:
        return None
    finally:
        plt.close("all")
