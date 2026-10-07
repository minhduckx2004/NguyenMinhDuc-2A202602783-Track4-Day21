"""Topic A: measure how yaw calibration drift moves object LiDAR points out of 2D boxes.

Run from the repo root:
    python -m src.exp_yaw_sweep --data-root data/kitti_mini --frames 000008 000011 000049
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from starter.datasets import load_frame
from starter.projection import perturb_extrinsic, project_velo_to_image, velo_to_cam

CLASSES = ("Car", "Van", "Pedestrian", "Cyclist")


def points_in_box(points_cam: np.ndarray, obj) -> np.ndarray:
    """Return a mask for camera-frame points inside one KITTI 3D label box."""
    h, w, l = obj.dimensions
    c, s = np.cos(obj.rotation_y), np.sin(obj.rotation_y)
    r = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    local = (points_cam - obj.location) @ r
    return (
        (np.abs(local[:, 0]) <= l / 2)
        & (local[:, 1] <= 0)
        & (local[:, 1] >= -h)
        & (np.abs(local[:, 2]) <= w / 2)
    )


def distance_bin(distance_m: float) -> str:
    if distance_m < 15:
        return "00-15m"
    if distance_m < 30:
        return "15-30m"
    return "30m+"


def run_one(fr: dict, yaw_deg: float) -> list[dict]:
    finite = np.isfinite(fr["points"]).all(axis=1)
    pts = fr["points"][finite]
    cam_true = velo_to_cam(pts[:, :3], fr["calib"])
    calib = perturb_extrinsic(fr["calib"], yaw_deg=yaw_deg)
    uv, _, mask = project_velo_to_image(pts, calib, fr["image"].shape)

    uv_all = np.full((len(pts), 2), np.nan)
    uv_all[mask] = uv

    rows = []
    for i, obj in enumerate(fr["labels"]):
        if obj.type not in CLASSES:
            continue
        sel = points_in_box(cam_true, obj) & mask
        obj_pts = int(sel.sum())
        if obj_pts == 0:
            continue
        u, v = uv_all[sel, 0], uv_all[sel, 1]
        x1, y1, x2, y2 = obj.bbox
        hits = int(((u >= x1) & (u <= x2) & (v >= y1) & (v <= y2)).sum())
        distance_m = float(np.hypot(obj.location[0], obj.location[2]))
        rows.append(
            {
                "object_id": i,
                "class": obj.type,
                "distance_bin": distance_bin(distance_m),
                "distance_m": round(distance_m, 1),
                "n_points": len(pts),
                "inside_image": int(mask.sum()),
                "object_points": obj_pts,
                "hits": hits,
                "hit_ratio": round(hits / obj_pts, 4),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep yaw drift and measure object-point hit ratio.")
    parser.add_argument("--data-root", default="data/kitti_mini", help="Dataset root.")
    parser.add_argument("--frames", nargs="+", default=["000008", "000011", "000049"], help="Frame ids.")
    parser.add_argument("--yaw-levels", nargs="+", type=float, default=[0, 0.5, 1, 2, 3], help="Yaw drift levels in degrees.")
    parser.add_argument("--out", default="results/yaw_perturb_sweep.csv", help="Output CSV path.")
    args = parser.parse_args()

    rows = []
    for frame in args.frames:
        fr = load_frame(args.data_root, frame)
        for yaw in args.yaw_levels:
            object_rows = run_one(fr, yaw)
            total_obj = sum(r["object_points"] for r in object_rows)
            total_hits = sum(r["hits"] for r in object_rows)
            summary = {
                "dataset": Path(args.data_root).name,
                "frame": frame,
                "yaw_deg": yaw,
                "group": "all",
                "object_id": "",
                "class": "all",
                "distance_bin": "all",
                "distance_m": "",
                "n_points": object_rows[0]["n_points"] if object_rows else len(fr["points"]),
                "inside_image": object_rows[0]["inside_image"] if object_rows else 0,
                "object_points": total_obj,
                "hits": total_hits,
                "hit_ratio": round(total_hits / total_obj, 4) if total_obj else float("nan"),
            }
            rows.append(summary)
            print(summary)
            for row in object_rows:
                rows.append({"dataset": Path(args.data_root).name, "frame": frame, "yaw_deg": yaw, "group": "object", **row})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"-> {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
