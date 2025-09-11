#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
from config import DATASET_ROOT, DATASET_NAME, DATASET_PATH, DATA_VARIANT

# ===== User-configurable parameters =====
TEST_NAME: str = "FullSet_QuarterRes-1009_145116"
STEPS: int = 100000
CHECKPOINT: str = str(DATASET_PATH / "3dgrut_runs" / DATA_VARIANT / TEST_NAME / f"ours_{STEPS}" / f"ckpt_{STEPS}.pt")
OUT_DIR: str = str(DATASET_PATH / "3dgrut_runs" / DATA_VARIANT / "eval")
# =======================================


def main() -> None:
    project_dir: Path = Path.home() / "Research" / "gaussian-splats" / "3dgrut"
    if not project_dir.is_dir():
        print(f"Error: Directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    # Use login shell (-l) semantics to ensure ~/.bashrc is sourced, then source conda.sh explicitly.
    # This makes conda activation reliable even when launched from other environments (e.g., uv).
    train_cmd = (
        'source "$(conda info --base)/etc/profile.d/conda.sh" && '
        'conda activate 3dgrut && '
        'python render.py '
        '--checkpoint '
        f'{CHECKPOINT} '
        '--out-dir '
        f'{OUT_DIR} '    
        '--fisheye-mode '
    )

    try:
        result = subprocess.run(
            ["bash", "-lc", train_cmd],
            cwd=project_dir,
            check=False,
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: bash not found on this system.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


