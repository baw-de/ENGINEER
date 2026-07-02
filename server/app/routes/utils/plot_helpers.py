import contextlib
import io
import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

_PLOT_OBJECTS: dict[str, Any] = {}
_PLOT_SVG_BYTES: dict[str, bytes] = {}

_SHARED_PLOT_DIR = Path(os.environ.get("PLOT_CACHE_DIR", "/tmp/labyrinth-plots")).expanduser()
try:
    _SHARED_PLOT_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass


def _shared_plot_path(plot_id: str) -> Path:
    return _SHARED_PLOT_DIR / f"{plot_id}.svg"


def store_plot_source(plot_id: str, obj: Any) -> None:
    # Stores the latest computed object for a plot ID.
    _PLOT_OBJECTS[plot_id] = obj


def store_plot_svg_bytes(plot_id: str, svg_bytes: bytes | None) -> None:
    # Stores rendered SVG bytes for plot IDs that are not object-based.
    if svg_bytes:
        _PLOT_SVG_BYTES[plot_id] = svg_bytes
        try:
            _shared_plot_path(plot_id).write_bytes(svg_bytes)
        except OSError:
            pass
    else:
        _PLOT_SVG_BYTES.pop(plot_id, None)
        try:
            _shared_plot_path(plot_id).unlink()
        except OSError:
            pass


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

        file_path = _shared_plot_path(plot_id)
        if file_path.is_file():
            try:
                return file_path.read_bytes()
            except OSError:
                pass

        return None
    except Exception:
        return None
    finally:
        plt.close("all")
