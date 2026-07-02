"""
Created on Fri Apr 10 12:14:14 2026

@author: morenos

Labyrinth weir STL generator.

Single entry point: `generate_labyrinth_geometry(D, W, alpha, B, t, P, filename)`
Builds the geometry of a trapezoidal labyrinth weir from its dimensional
parameters and writes a watertight binary STL mesh ready for download.
"""

import struct

import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _offset_polyline(x, y, d):
    """
    Compute the parallel offset of a polyline at distance `d`.
        d > 0  -> left side  (CCW normal of each segment)
        d < 0  -> right side
    Uses miter joins at interior vertices.
    """
    pts = np.column_stack([x, y]).astype(float)
    n = len(pts)
    out = np.zeros_like(pts)

    edges = pts[1:] - pts[:-1]
    lens = np.linalg.norm(edges, axis=1)
    e_u = edges / lens[:, None]
    # "Left" normal: rotate 90° CCW  (x, y) -> (-y, x)
    normals = np.column_stack([-e_u[:, 1], e_u[:, 0]])

    # End points: offset perpendicular to the adjacent segment
    out[0] = pts[0] + d * normals[0]
    out[-1] = pts[-1] + d * normals[-1]

    # Interior vertices: miter join
    for i in range(1, n - 1):
        n1, n2 = normals[i - 1], normals[i]
        bis = n1 + n2
        denom = 1.0 + float(n1 @ n2)
        if abs(denom) < 1e-12:
            out[i] = pts[i] + d * n1
        else:
            out[i] = pts[i] + d * bis / denom
    return out[:, 0], out[:, 1]


def _build_polyline(D, W, alpha, B):
    """
    Build the crest polyline of the trapezoidal labyrinth weir in plan view.

    The labyrinth is built as `n` symmetric teeth with (n-1) front walls
    between them (no front wall at the very start or end). Each tooth =
    upstream slope + back wall + downstream slope. Labyrinth width:
    W_lab = n * w_cycle - D.

    If `W` does not allow an integer number of teeth, the cycles are centered
    and the leftover length is distributed as two straight extensions
    (at y = 0) on each side.
    """
    alpha_rad = np.radians(alpha)
    proj = B * np.tan(alpha_rad)
    side_len = B / np.cos(alpha_rad)

    w_cycle = 2 * D + 2 * proj
    L_cycle = 2 * D + 2 * side_len

    n_exact = W / w_cycle
    n_teeth = int(np.floor(n_exact))
    if n_teeth < 1:
        raise ValueError(f"W={W} is too small for a single tooth (w_cycle={w_cycle:.4f}, n_exact={n_exact:.3f}). Reduce D, B or alpha, or increase W.")

    W_lab = n_teeth * w_cycle - D  # width occupied by the symmetric teeth
    pad = (W - W_lab) / 2.0  # straight extension on each side

    xs, ys = [0.0], [0.0]
    x = 0.0

    # Left straight extension
    if pad > 0:
        x += pad
        xs.append(x)
        ys.append(0.0)

    # First tooth: upstream slope + back wall + downstream slope (no leading front wall)
    x += proj
    xs.append(x)
    ys.append(B)
    x += D
    xs.append(x)
    ys.append(B)
    x += proj
    xs.append(x)
    ys.append(0.0)

    # Remaining teeth: front wall + upstream slope + back wall + downstream slope
    for _ in range(n_teeth - 1):
        x += D
        xs.append(x)
        ys.append(0.0)
        x += proj
        xs.append(x)
        ys.append(B)
        x += D
        xs.append(x)
        ys.append(B)
        x += proj
        xs.append(x)
        ys.append(0.0)

    # Right straight extension
    if pad > 0:
        x += pad
        xs.append(x)
        ys.append(0.0)

    L_total = n_teeth * L_cycle - D + 2 * pad

    info = {
        "n_exact": n_exact,
        "n_cycles": n_teeth,
        "n_teeth": n_teeth,
        "w_cycle": w_cycle,
        "L_cycle": L_cycle,
        "L_total": L_total,
        "W_used": W,
        "W_lab": W_lab,
        "pad": pad,
        "L_over_W": L_total / W,
        "proj": proj,
        "side_len": side_len,
    }
    return np.array(xs), np.array(ys), info


def _cap_rings(x, y, xL, yL, P, r, n_theta=14):
    """
    Generate rings of a half-cylinder of radius `r` swept along the centerline,
    whose base sits at z = P - r and top at z = P. Each ring corresponds to
    an angle theta in [-pi/2, +pi/2] around the cylinder axis.

    Convention:
        theta = -pi/2  -> coincides with the right offset (xR, z = P-r)
        theta =  0     -> top of the dome (centerline, z = P)
        theta = +pi/2  -> coincides with the left offset (xL, z = P-r)

    Returns: list of (cx, cy, cz) arrays of length n.
    """
    dxL = xL - x
    dyL = yL - y
    thetas = np.linspace(-np.pi / 2, np.pi / 2, n_theta + 1)
    rings = []
    for th in thetas:
        s = np.sin(th)
        c = np.cos(th)
        cx = x + s * dxL
        cy = y + s * dyL
        cz = np.full_like(x, (P - r) + r * c)
        rings.append((cx, cy, cz))
    return rings


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def generate_labyrinth_geometry(D, W, alpha, B, t=0.01, P=0.253, filename="labyrinth_weir.stl", n_theta=14):
    """
    Generate a trapezoidal labyrinth weir as a watertight binary STL mesh.

    Parameters
    ----------
    D : float
        Front/back wall width [m].
    W : float
        Total channel width [m].
    alpha : float
        Sidewall angle [degrees].
    B : float
        Depth in flow direction [m].
    t : float, optional
        Wall thickness [m]. Default 0.01 (Ts = 0.01 m).
    P : float, optional
        Weir height [m]. Default 0.253.
    filename : str, optional
        Output STL file path. Default "labyrinth_weir.stl".
    n_theta : int, optional
        Number of angular subdivisions of the rounded crest dome. Default 14.

    Returns
    -------
    filename : str
        Path of the written STL file.
    info : dict
        Dictionary with derived geometric quantities (number of cycles,
        cycle width, total crest length, L/W ratio, etc.).
    """
    # 1) Build centerline polyline and left/right offsets for wall thickness
    x, y, info = _build_polyline(D, W, alpha, B)
    xL, yL = _offset_polyline(x, y, +t / 2)
    xR, yR = _offset_polyline(x, y, -t / 2)

    n = len(xL)
    r = t / 2
    z_body = P - r

    # 2) Triangulate: each entry is (v0, v1, v2) in CCW order viewed from outside
    triangles = []

    def quad_to_tris(a, b, c, d):
        triangles.append((a, b, c))
        triangles.append((a, c, d))

    # --- Vertical body and bottom cap ---
    for i in range(n - 1):
        # Outer left face (normal pointing outward on the left side)
        quad_to_tris(
            (xL[i], yL[i], 0.0),
            (xL[i], yL[i], z_body),
            (xL[i + 1], yL[i + 1], z_body),
            (xL[i + 1], yL[i + 1], 0.0),
        )
        # Outer right face
        quad_to_tris(
            (xR[i], yR[i], 0.0),
            (xR[i + 1], yR[i + 1], 0.0),
            (xR[i + 1], yR[i + 1], z_body),
            (xR[i], yR[i], z_body),
        )
        # Bottom cap (z = 0, normal pointing downward)
        quad_to_tris(
            (xL[i], yL[i], 0.0),
            (xL[i + 1], yL[i + 1], 0.0),
            (xR[i + 1], yR[i + 1], 0.0),
            (xR[i], yR[i], 0.0),
        )

    # --- Dome: strip of quads between consecutive rings ---
    rings = _cap_rings(x, y, xL, yL, P, r, n_theta=n_theta)
    for j in range(len(rings) - 1):
        cxA, cyA, czA = rings[j]
        cxB, cyB, czB = rings[j + 1]
        for i in range(n - 1):
            # Winding so the normal points outward from the dome
            quad_to_tris(
                (cxA[i], cyA[i], czA[i]),
                (cxA[i + 1], cyA[i + 1], czA[i + 1]),
                (cxB[i + 1], cyB[i + 1], czB[i + 1]),
                (cxB[i], cyB[i], czB[i]),
            )

    # --- End caps: rectangle (0..z_body) + half-disk (fan) ---
    for i_end, sign in ((0, -1), (-1, +1)):
        # Rectangle at the end. `sign` is the outward normal direction
        # (-x at the start, +x at the end).
        if sign < 0:
            quad_to_tris(
                (xL[i_end], yL[i_end], 0.0),
                (xL[i_end], yL[i_end], z_body),
                (xR[i_end], yR[i_end], z_body),
                (xR[i_end], yR[i_end], 0.0),
            )
        else:
            quad_to_tris(
                (xR[i_end], yR[i_end], 0.0),
                (xR[i_end], yR[i_end], z_body),
                (xL[i_end], yL[i_end], z_body),
                (xL[i_end], yL[i_end], 0.0),
            )
        # Half-disk fan around the end center (x[i_end], y[i_end], z_body)
        cx0, cy0 = float(x[i_end]), float(y[i_end])
        center = (cx0, cy0, z_body)
        for j in range(len(rings) - 1):
            ax_, ay_, az_ = (float(rings[j][0][i_end]), float(rings[j][1][i_end]), float(rings[j][2][i_end]))
            bx_, by_, bz_ = (float(rings[j + 1][0][i_end]), float(rings[j + 1][1][i_end]), float(rings[j + 1][2][i_end]))
            if sign < 0:
                triangles.append((center, (ax_, ay_, az_), (bx_, by_, bz_)))
            else:
                triangles.append((center, (bx_, by_, bz_), (ax_, ay_, az_)))

    # 3) Compute normals and write binary STL
    def normal(a, b, c):
        ax, ay, az = a
        bx, by, bz = b
        cx, cy, cz = c
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        L = (nx * nx + ny * ny + nz * nz) ** 0.5
        if L == 0:
            return 0.0, 0.0, 0.0
        return nx / L, ny / L, nz / L

    with open(filename, "wb") as f:
        f.write(b"\0" * 80)  # 80-byte header
        f.write(struct.pack("<I", len(triangles)))  # number of triangles
        for a, b, c in triangles:
            nx, ny, nz = normal(a, b, c)
            f.write(struct.pack("<12fH", nx, ny, nz, a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2], 0))

    info["filename"] = filename
    info["n_triangles"] = len(triangles)
    return filename, info


# ---------------------------------------------------------------------------
# Standalone test run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Trapezoidal labyrinth weir parameters
    D = 0.04  # front/back wall width [m]
    W = 1.25  # total channel width [m]
    alpha = 8.32  # sidewall angle [deg]
    B = 0.59  # depth in flow direction [m]
    t = 0.01  # wall thickness [m]
    P = 0.253  # weir height [m]

    fname, info = generate_labyrinth_geometry(D, W, alpha, B, t=t, P=P, filename="labyrinth_weir.stl")

    print("=" * 50)
    print("  TRAPEZOIDAL LABYRINTH WEIR GEOMETRY")
    print("=" * 50)
    print(f"  D (front/back wall)   = {D} m")
    print(f"  W (total width)       = {W} m")
    print(f"  alpha (sidewall)      = {alpha} deg")
    print(f"  B (depth, flow dir.)  = {B} m")
    print(f"  t (wall thickness)    = {t} m")
    print(f"  P (weir height)       = {P} m")
    print("-" * 50)
    print(f"  lateral projection    = B*tan(a) = {info['proj']:.4f} m")
    print(f"  sidewall length       = B/cos(a) = {info['side_len']:.4f} m")
    print(f"  cycle width w         = {info['w_cycle']:.4f} m")
    print(f"  crest per cycle Lc    = {info['L_cycle']:.4f} m")
    print(f"  exact n_cycles        = {info['n_exact']:.3f}")
    print(f"  drawn teeth           = {info['n_teeth']}")
    print(f"  width used by lab.    = {info['W_lab']:.4f} m")
    print(f"  straight pad/side     = {info['pad']:.4f} m  ({info['pad'] * 1000:.2f} mm)")
    print(f"  total crest L         = {info['L_total']:.4f} m")
    print(f"  L / W                 = {info['L_over_W']:.3f}")
    print("=" * 50)
    print(f"  STL exported: {fname}  ({info['n_triangles']} triangles)")
