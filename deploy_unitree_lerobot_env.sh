#!/usr/bin/env bash
# =============================================================================
# Unitree LeRobot — fresh machine setup for training (LeRobot + unitree_lerobot)
#
# Usage (from this repository root, next to unitree_lerobot/):
#   chmod +x deploy_unitree_lerobot_env.sh
#   ./deploy_unitree_lerobot_env.sh
#
# Optional environment variables:
#   CONDA_ENV_NAME    default: unitree_lerobot
#   PYTHON_VERSION    default: 3.10
#   PYTORCH_INDEX_URL e.g. https://download.pytorch.org/whl/cu124 (match your CUDA)
#
# Notes:
#   - Does not install unitree_sdk2_python (install separately for robot/DDS/sim).
#   - Install Isaac Sim per official docs if you need simulation.
#   - Requires conda or mamba (Miniforge recommended).
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Script lives at repository root (Unitree_VLA), not under scripts/.
REPO_ROOT="${SCRIPT_DIR}"
UNITREE_LEROBOT_PKG="${REPO_ROOT}/unitree_lerobot"
LEROBOT_SRC="${UNITREE_LEROBOT_PKG}/unitree_lerobot/lerobot"

CONDA_ENV_NAME="${CONDA_ENV_NAME:-unitree_lerobot}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"

die() { echo "ERROR: $*" >&2; exit 1; }

command -v conda >/dev/null 2>&1 || die "conda not found. Install Miniconda, Miniforge, or Mambaforge first."

[[ -f "${LEROBOT_SRC}/pyproject.toml" ]] || die "LeRobot source not found: ${LEROBOT_SRC} (run this script from the repository root)"
[[ -f "${UNITREE_LEROBOT_PKG}/pyproject.toml" ]] || die "unitree_lerobot pyproject.toml not found: ${UNITREE_LEROBOT_PKG}"

echo "=========================================="
echo " Unitree LeRobot environment (training)"
echo "=========================================="
echo "Repo root:       ${REPO_ROOT}"
echo "LeRobot source:  ${LEROBOT_SRC}"
echo "Conda env:       ${CONDA_ENV_NAME}"
echo "Python:          ${PYTHON_VERSION}"
echo "=========================================="

if conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME}"; then
  echo "Conda env already exists: ${CONDA_ENV_NAME} (reusing)"
else
  echo "Creating conda env ${CONDA_ENV_NAME} (python=${PYTHON_VERSION})..."
  conda create -y -n "${CONDA_ENV_NAME}" "python=${PYTHON_VERSION}"
fi

# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV_NAME}"

echo "Upgrading pip..."
python -m pip install -U pip setuptools wheel

echo "Installing conda packages (pinocchio, ffmpeg)..."
conda install -y -c conda-forge pinocchio "ffmpeg>=7" || conda install -y -c conda-forge pinocchio ffmpeg

if [[ -n "${PYTORCH_INDEX_URL:-}" ]]; then
  echo "Installing PyTorch with PYTORCH_INDEX_URL=${PYTORCH_INDEX_URL}..."
  pip install torch torchvision --index-url "${PYTORCH_INDEX_URL}"
fi

echo "Installing LeRobot (editable)..."
pip install -e "${LEROBOT_SRC}"

echo "Installing unitree_lerobot (editable)..."
pip install -e "${UNITREE_LEROBOT_PKG}"

POST="${UNITREE_LEROBOT_PKG}/scripts/DEPLOY_NOTES.txt"
cat > "${POST}" <<EOF
Generated: $(date -Iseconds)
Conda env: ${CONDA_ENV_NAME}

Activate:
  conda activate ${CONDA_ENV_NAME}

Training (example):
  cd ${LEROBOT_SRC}/src/lerobot/scripts
  python lerobot_train.py --help

Hugging Face (datasets / gated models):
  huggingface-cli login

PyTorch / CUDA (example):
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
EOF

echo ""
echo "=========================================="
echo "Done. Notes written to: ${POST}"
echo "Next: conda activate ${CONDA_ENV_NAME}"
echo "=========================================="
