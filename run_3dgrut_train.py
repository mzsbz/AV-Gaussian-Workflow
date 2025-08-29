#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

# ===== User-configurable parameters =====
# Change these to adjust the training run without editing the command below.
DATASET_NAME = "YJP-Lvl04_250828_DSLR"
DATA_VARIANT = "oddset_quarterres"
DATA_PATH: str = f"/home/pc-04/Research/_datasets/{DATASET_NAME}/colmap_runs/{DATA_VARIANT}"
OUT_DIR: str = f"/home/pc-04/Research/_datasets/{DATASET_NAME}/3dgrut_runs/"
EXPERIMENT_NAME: str = f"{DATA_VARIANT}"
DOWNSAMPLE_FACTOR: int = 1
ITERATIONS: int = 30000
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
        'python train.py '
        '--config-name apps/colmap_3dgut_mcmc.yaml '
        f'path={DATA_PATH} '
        f'out_dir={OUT_DIR} '
        f'experiment_name={EXPERIMENT_NAME} '
        f'dataset.downsample_factor={DOWNSAMPLE_FACTOR} '
        'export_ply.enabled=true '
        'test_last=false '
        f'n_iterations={ITERATIONS}'        
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


