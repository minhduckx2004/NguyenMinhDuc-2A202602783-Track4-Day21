"""Plot the Topic A yaw sweep result.

Run from the repo root:
    python -m src.plot_yaw_sweep
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    df = pd.read_csv("results/yaw_perturb_sweep.csv", dtype={"frame": str})
    summary = df[df["group"] == "all"].copy()

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for frame, group in summary.groupby("frame"):
        ax.plot(group["yaw_deg"], 100 * group["hit_ratio"], marker="o", label=f"frame {frame}")
    ax.set_xlabel("Yaw drift (deg)")
    ax.set_ylabel("Object LiDAR points inside 2D boxes (%)")
    ax.set_ylim(0, 105)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()

    out = Path("results/figures/yaw_sweep.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
