"""Create a side-by-side failure image for yaw calibration drift.

Run from the repo root:
    python -m src.make_failure_case
"""
from pathlib import Path

import cv2
import numpy as np

from starter.datasets import load_frame
from starter.projection import draw_box2d, overlay_points, perturb_extrinsic, project_velo_to_image


def render(frame: str, yaw_deg: float) -> np.ndarray:
    fr = load_frame("data/kitti_mini", frame)
    calib = perturb_extrinsic(fr["calib"], yaw_deg=yaw_deg)
    uv, depth, _ = project_velo_to_image(fr["points"], calib, fr["image"].shape)
    vis = overlay_points(fr["image"], uv, depth)
    for obj in fr["labels"]:
        vis = draw_box2d(vis, obj.bbox, label=obj.type)
    cv2.putText(vis, f"yaw {yaw_deg:g} deg", (24, 36), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
    cv2.putText(vis, f"yaw {yaw_deg:g} deg", (24, 36), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 220), 2)
    return vis


def main() -> None:
    frame = "000011"
    ok = render(frame, 0)
    fail = render(frame, 2)
    combined = np.hstack([ok, fail])
    cv2.putText(combined, "baseline", (24, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(
        combined,
        "failure: points slide out of narrow pedestrian boxes",
        (ok.shape[1] + 24, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    out = Path("results/figures/fail_01_kitti_yaw2_pedestrians.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), combined)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
