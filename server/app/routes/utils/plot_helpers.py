import contextlib
import io
from typing import Any

import matplotlib.pyplot as plt

_PLOT_OBJECTS: dict[str, Any] = {}
_PLOT_SVG_BYTES: dict[str, bytes] = {}


def store_plot_source(plot_id: str, obj: Any) -> None:
    # Stores the latest computed object for a plot ID.
    _PLOT_OBJECTS[plot_id] = obj


def store_plot_svg_bytes(plot_id: str, svg_bytes: bytes | None) -> None:
    # Stores rendered SVG bytes for plot IDs that are not object-based.
    if svg_bytes:
        _PLOT_SVG_BYTES[plot_id] = svg_bytes
    else:
        _PLOT_SVG_BYTES.pop(plot_id, None)


def capture_current_figure_svg_bytes() -> bytes | None:
    # Captures the currently active matplotlib figure as SVG bytes.
    fig = plt.gcf()
    if fig is None:
        return None
    if not fig.axes:
        return None
    svg_buf = io.BytesIO()
    fig.savefig(svg_buf, format="svg", bbox_inches="tight")
    svg_buf.seek(0)
    return svg_buf.getvalue()


def generate_geometry_plot_svg(plot_id: str = "default") -> bytes | None:
    # Generates SVG bytes for the plot ID, or None if no source is available.
    try:
        cached_svg = _PLOT_SVG_BYTES.get(plot_id)
        if cached_svg:
            return cached_svg

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
